import sys
import os
import logging
from skidl import Part, Net, search  # 'search' is the key for dynamic discovery

# --- PATH INJECTION ---
# Ensures root is in path so this can be imported by core_engine/ scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

"""
PragyanAI Symbol Macros
Refined for cloud-deployment with Dynamic Discovery logic.
"""

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    """
    v33 = Net('3V3')
    
    # Instantiate Parts
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring Logic
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32-S3.
    Uses 'search' to find the actual part name on the server's library.
    """
    mcu = None
    lib = 'MCU_Espressif'
    
    try:
        # 1. Search the library for the most appropriate S3 variant
        matches = search(lib, 'ESP32-S3-WROOM')
        
        if matches:
            # Pick the first match found in the library
            target_name = matches[0]
            logger.info(f"Dynamic Discovery matched: {target_name}")
            mcu = Part(lib, target_name, footprint='RF_Module:ESP32-S3-WROOM-1-N8')
        else:
            # 2. Fallback to older ESP32 if S3 is missing from server's version
            logger.warning("No S3 variant found. Falling back to ESP32-WROOM-32.")
            mcu = Part(lib, 'ESP32-WROOM-32', footprint='RF_Module:ESP32-WROOM-32')
            
    except Exception as e:
        logger.error(f"Symbol Discovery Error: {e}")
        # 3. Hard-coded safety fallback
        mcu = Part(lib, 'ESP32-WROOM-32', footprint='RF_Module:ESP32-WROOM-32')

    # Standard Supporting Passives
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring Power
    mcu['3V3'] += v33_net
    mcu['GND'] += gnd_net
    c_dec[1, 2] += v33_net, gnd_net
    
    # Enable Pin (EN) pull-up
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    
    # Robust Pin Access: Try name 'EN', fallback to pin index 3 (standard for ESP32)
    try:
        mcu['EN'] += r_en[1]
    except:
        mcu[3] += r_en[1]
        
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Macro: Standard 4.7k Pull-up resistors for I2C Bus."""
    r_sda = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    
    sda_net += r_sda[1]
    scl_net += r_scl[1]
    r_sda[2] += vcc_net
    r_scl[2] += vcc_net
    
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="RED"):
    """Macro: LED with current limiting resistor."""
    led = Part('Device', 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part('Device', 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    
    signal_net += res[1]
    res[2]     += led[1]
    led[2]     += gnd_net
    
    return led, res
    
    
