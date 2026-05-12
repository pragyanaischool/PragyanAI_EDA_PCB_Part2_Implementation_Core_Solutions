import pytest
import os
import pandas as pd
from core_engine.bom_manager import BOMManager

@pytest.fixture
def manager():
    """Fixture to initialize the BOMManager."""
    return BOMManager()

@pytest.fixture
def sample_plan():
    """Provides a standardized architecture plan for testing."""
    return {
        "project_name": "Hydroponics_V1",
        "mcu": {
            "family": "ESP32-S3",
            "mpn": "ESP32-S3-WROOM-1-N8",
            "footprint": "RF_Module:ESP32-S3-WROOM-1-N8"
        },
        "power_tree": [
            {
                "component": "Buck Converter",
                "mpn": "LM2596S-5.0",
                "footprint": "Package_TO_SOT_SMD:TO-263-5_TabPin3"
            },
            {
                "component": "LDO",
                "mpn": "AMS1117-3.3",
                "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
            }
        ]
    }

def test_bom_csv_generation(manager, sample_plan):
    """Verifies that the manager can write a physical CSV file."""
    output_path = "tests/temp_test_bom.csv"
    
    # Ensure any previous test file is removed
    if os.path.exists(output_path):
        os.remove(output_path)
        
    manager.export_bom(sample_plan, filename=output_path)
    
    assert os.path.exists(output_path)
    
    # Check content validity
    df = pd.read_csv(output_path)
    assert not df.empty
    assert "Designator" in df.columns
    assert "MPN" in df.columns
    
    # Clean up
    os.remove(output_path)

def test_bom_quantity_calculation(manager, sample_plan):
    """Ensures the quantity logic correctly identifies parts."""
    output_path = "tests/qty_test.csv"
    manager.export_bom(sample_plan, filename=output_path)
    
    df = pd.read_csv(output_path)
    
    # We expect 1 MCU and 2 power components in this plan
    # Total rows in BOM should match unique parts
    assert len(df) >= 3
    
    # Verify the specific MPN is present
    assert "ESP32-S3-WROOM-1-N8" in df['MPN'].values
    
    os.remove(output_path)

def test_bom_empty_plan_handling(manager):
    """Checks if the manager handles malformed or empty plans gracefully."""
    empty_plan = {}
    output_path = "tests/empty_test.csv"
    
    with pytest.raises(KeyError):
        # The manager should fail if critical keys like 'mcu' are missing
        manager.export_bom(empty_plan, filename=output_path)

def test_bom_data_types(manager, sample_plan):
    """Ensures that numeric values in the BOM are stored correctly."""
    output_path = "tests/dtype_test.csv"
    manager.export_bom(sample_plan, filename=output_path)
    
    df = pd.read_csv(output_path)
    # Quantity should always be an integer
    assert pd.api.types.is_integer_dtype(df['Quantity'])
    
    os.remove(output_path)
  
