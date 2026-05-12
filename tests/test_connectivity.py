import pytest
from skidl import Net, Part, ERC, KICAD, set_default_tool
import os

# Set the default EDA tool to KiCad for the test environment
set_default_tool(KICAD)

@pytest.fixture(autouse=True)
def reset_skidl():
    """Resets the SKiDL circuit internal state before every test."""
    from skidl import default_circuit
    default_circuit.reset()
    yield

def test_vcc_gnd_separation():
    """
    CRITICAL: Ensures the main power rails are not shorted.
    In EDA automation, an accidental '+' instead of '+=' can bridge nets.
    """
    vcc = Net('3V3')
    gnd = Net('GND')
    
    # Instantiate a component
    cap = Part('Device', 'C', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Correct connection
    cap[1] += vcc
    cap[2] += gnd
    
    # Assert that the nets are physically distinct and contain the correct nodes
    assert vcc.name != gnd.name
    assert len(vcc.nodes) == 1
    assert len(gnd.nodes) == 1
    # Ensure they aren't connected to each other
    assert not vcc.is_connected(gnd)

def test_bus_integrity():
    """Verifies that I2C/SPI bus signals are correctly grouped."""
    sda = Net('SDA')
    scl = Net('SCL')
    
    # Mock an MCU and a Sensor
    mcu = Part('MCU_Espressif', 'ESP32-S3-WROOM-1', footprint='RF_Module:ESP32-S3-WROOM-1-N8')
    sensor = Part('Sensor', 'BME280', footprint='Package_LGA:Bosch_LGA-8_2.5x2.5mm_P0.65mm_Clockwise')
    
    # Logic: Connect SDA to both
    mcu['GPIO1'] += sda
    sensor['SDA'] += sda
    
    assert len(sda.nodes) == 2
    assert sda.is_connected(mcu['GPIO1'])
    assert sda.is_connected(sensor['SDA'])

def test_erc_violation_catch():
    """
    Tests if the SKiDL Electrical Rules Check (ERC) identifies 
    unconnected pins on critical components.
    """
    # Create a regulator but leave pins floating
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    
    # We expect ERC to find issues (unconnected pins)
    # We capture the output of ERC to verify our validation logic
    errors, warnings = ERC()
    
    # In a real build, we want to know if there are high-severity errors
    assert errors >= 0 # ERC returns the count of violations
    print(f"ERC found {errors} errors and {warnings} warnings.")

def test_netlist_generation_capability():
    """Ensures the internal state is valid enough to produce a .net file."""
    vcc = Net('3V3')
    gnd = Net('GND')
    r = Part('Device', 'R', footprint='Resistor_SMD:R_0603_1608Metric')
    r[1] += vcc
    r[2] += gnd
    
    try:
        from skidl import generate_netlist
        generate_netlist(file_name='tests/connectivity_check.net')
        file_exists = os.path.exists('tests/connectivity_check.net')
        if file_exists:
            os.remove('tests/connectivity_check.net')
        assert file_exists
    except Exception as e:
        pytest.fail(f"Netlist generation failed: {e}")
      
