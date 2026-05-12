import pytest
import os
import json
from core_engine.footprint_mapper import FootprintMapper

@pytest.fixture
def mapper():
    """Fixture to initialize the FootprintMapper for each test."""
    return FootprintMapper()

def test_mapper_initialization(mapper):
    """Verify that the mapper loads its internal mapping database."""
    assert mapper.mapping_db is not None
    assert isinstance(mapper.mapping_db, dict)

def test_mcu_exact_match(mapper):
    """Test mapping for a standard ESP32-S3 requirement."""
    plan = {
        "mcu": {
            "family": "ESP32-S3",
            "package": "WROOM"
        }
    }
    result = mapper.assign_footprints(plan)
    
    assert "mcu" in result
    # Verify it pulled the specific KiCad library path
    assert "RF_Module:ESP32-S3-WROOM-1" in result["mcu"]["footprint"]
    assert result["mcu"]["mpn"] == "ESP32-S3-WROOM-1-N8"

def test_power_component_mapping(mapper):
    """Test mapping for power tree elements like LDOs or Bucks."""
    plan = {
        "power_tree": [
            {
                "component": "LDO Regulator",
                "output_v": 3.3
            }
        ]
    }
    result = mapper.assign_footprints(plan)
    
    # Check if the mapper identified the common AMS1117 footprint
    ldo_mapping = result["power_tree"][0]
    assert "SOT-223" in ldo_mapping["footprint"]
    assert "AMS1117" in ldo_mapping["mpn"]

def test_fallback_logic(mapper):
    """
    Ensures that if the AI suggests an unknown part, 
    the mapper provides a 'Generic' footprint instead of crashing.
    """
    plan = {
        "mcu": {
            "family": "QuantumChip-9000" # Non-existent part
        }
    }
    result = mapper.assign_footprints(plan)
    
    assert "Generic" in result["mcu"]["footprint"]
    assert "UNKNOWN" in result["mcu"]["mpn"]

def test_interface_consistency(mapper):
    """Checks if defined interfaces (I2C/SPI) are flagged for the schematic gen."""
    plan = {
        "interfaces": {
            "Display": "I2C",
            "Sensor": "SPI"
        }
    }
    result = mapper.assign_footprints(plan)
    
    assert result["interfaces"]["Display"] == "I2C"
    assert result["interfaces"]["Sensor"] == "SPI"
  
