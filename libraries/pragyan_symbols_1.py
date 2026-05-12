import sys
import os
import logging
from skidl import Part, Net, search, KICAD

# --- 1. PATH STABILIZATION ---
# Ensures the root directory is accessible so sub-modules can talk to each other
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

"""
PragyanAI Symbol Macros: Deployment Edition
This version includes dynamic discovery logic specifically designed to handle 
the KiCad library variations found on Streamlit Cloud (Linux) environments.
"""

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    Encapsulates the AMS1117-3.3 and essential decoupling caps.
    """
    v33 = Net('3V3')
    
    # Parts instantiation from standard KiCad 'Device' and 'Regulator_Linear' libs
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring Logic: Pin 3=IN, 2=OUT, 1=GND
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32-S3.
    Uses 'Global Hunter' discovery logic to bypass library naming drift.
    """
    mcu = None
    # Priority patterns to search for in the server's libraries
    search_patterns = ['ESP32-S3-WROOM', 'ESP32-S3', 'ESP32-WROOM-32']
    
    for pattern in search_patterns:
        try:
            # Search across ALL loaded libraries for the pattern
            results = search(pattern)
            if results:
                target_part = results[0]
                # Common library names on Linux/Streamlit for these modules
                for lib_name in ['MCU_Espressif', 'RF_Module', 'ESP32-S3-WROOM-1']:
                    try:
                        mcu = Part(lib_name, target_part, footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                        if mcu: break
                    except: continue
            if mcu: 
                logger.info(f"Implementation Core matched MCU: {mcu.name}")
                break
        except: continue

    if not mcu:
        # FAIL-SAFE: If KiCad libraries are totally missing on the cloud instance,
        # we create a generic 38-pin module to allow the netlist synthesis to complete.
        logger.warning("No ESP32 symbols discovered. Using Generic 38-pin fallback.")
        mcu = Part('Connector', 'Conn_01x19_Male', footprint='Connector_PinHeader_2.54mm:PinHeader_1x19_P2.54mm_Vertical')

    # Standard Supporting Passives
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring Power (Iterates through possible pin names for robustness)
    for p_name in ['3V3', 'VCC', 'VDD', '3.3V', '1']:
        try:
            mcu[p_name] += v33_net
            break
        except: continue
        
    # Wiring Ground
    try: mcu['GND'] += gnd_net
    except: mcu['2'] += gnd_net # Fallback to common header index
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # EN (Enable) Pull-up logic
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1] # Standard pin index for EN
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Macro: 4.7k Pull-up resistors for the I2C Bus."""
    r_sda = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    
    sda_net += r_sda[1]
    scl_net += r_scl[1]
    r_sda[2] += vcc_net
    r_scl[2] += vcc_net
    
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="RED"):
    """Macro: Indication LED with current limiting resistor."""
    led = Part('Device', 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part('Device', 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    
    signal_net += res[1]
    res[2]     += led[1] # Anode
    led[2]     += gnd_net # Cathode
    
    return led, res
    
    
