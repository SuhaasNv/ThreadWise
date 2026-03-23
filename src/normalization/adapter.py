from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError

class StandardPerformanceModel(BaseModel):
    """
    Canonical schema for connection performance data.
    All vendor data must be normalized into this strict structure
    to guarantee logic engine integrity.
    """
    tension: float = Field(..., description="Tensile strength (compression/tension) in lbs")
    burst: float = Field(..., description="Internal yield/burst pressure in psi")
    collapse: float = Field(..., description="Collapse resistance in psi")

class VendorAdapter(ABC):
    """
    Abstract base class for all vendor normalization adapters.
    Ensures that regardless of what raw keys a vendor scraper returns,
    the output perfectly matches the StandardPerformanceModel rigid schema.
    """
    
    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Normalizes raw vendor data into the standard dictionary schema.
        
        Args:
            raw_data (Dict[str, Any]): The unnormalized data scraped from the vendor.
            
        Returns:
            Dict[str, float]: Standardized data matching the required schema.
        """
        pass
        
    def _validate_schema(self, normalized_data: dict) -> Dict[str, float]:
        """
        Helper method to strictly enforce the schema using Pydantic.
        Raises a Hard Stop 'ValueError' if normalization produced bad types.
        """
        try:
            model = StandardPerformanceModel(**normalized_data)
            # Use model_dump for Pydantic v2, fallback to dict() for v1
            return model.model_dump() if hasattr(model, 'model_dump') else model.dict()
        except ValidationError as e:
            raise ValueError(f"Normalization failed strict schema validation: {e}")

class VAMAdapter(VendorAdapter):
    """
    Adapter specifically for VAM vendor data.
    Maps VAM-specific site terminology to the ThreadWise canonical schema.
    """
    
    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Executes the mapping from VAM raw dictionaries to the System's standard.
        """
        # Even though vam_fetcher tries to output clean data, the Normalization layer 
        # acts as the ultimate defensive perimeter. We map potential variant keys here.
        normalized = {
            "tension": float(raw_data.get("tension") or raw_data.get("tensile_strength", 0.0)),
            "burst": float(raw_data.get("burst") or raw_data.get("internal_yield", 0.0)),
            "collapse": float(raw_data.get("collapse") or raw_data.get("collapse_resistance", 0.0))
        }
        
        # Hard Stop: Engineering logic cannot process 0.0 as a valid performance rating.
        if any(v <= 0.0 for v in normalized.values()):
            raise ValueError(f"VAM Normalization Error: Ambiguous, missing, or zero values detected. Raw input: {raw_data}")
            
        return self._validate_schema(normalized)


if __name__ == "__main__":
    # --- Simple Formatter Test Execution ---
    adapter = VAMAdapter()
    
    print("--- Running VAM Adapter Normalization Tests ---")
    
    # 1. Test Clean Mapping validation
    mock_clean_raw = {
        "tension": 345000.0,
        "burst": 12000.0,
        "collapse": 11500.0
    }
    print(f"\n✅ Testing Clean Scrape:\nInput: {mock_clean_raw}")
    print(f"Output: {adapter.normalize(mock_clean_raw)}")
    
    # 2. Test Dirty Mapping validation (Missing standard keys, but alternative keys exist)
    mock_dirty_raw = {
        "tensile_strength": "345000",
        "internal_yield": 12000.0,
        "collapse_resistance": "11500.0"
    }
    print(f"\n✅ Testing Dirty Scrape (String types + Alternate Keys):\nInput: {mock_dirty_raw}")
    print(f"Output: {adapter.normalize(mock_dirty_raw)}")
    
    # 3. Test Hard Stop Failure validation (Missing value)
    mock_fail_raw = {
        "tension": 345000.0,
        "burst": 12000.0
        # missing collapse entirely
    }
    print(f"\n❌ Testing 'Hard Stop' Catch (Missing Value):\nInput: {mock_fail_raw}")
    try:
        adapter.normalize(mock_fail_raw)
    except ValueError as e:
        print(f"Caught Expected Failure: {e}")
