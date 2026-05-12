import sys
import os
import logging
from skidl import Part, Net, search, KICAD

# --- 1. PATH STABILIZATION ---
# Ensures root is in path so sub-modules can be imported correctly in the cloud
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

"""
PragyanAI Symbol Macros: Modular Architecture
This file encapsulates hardware templates. By using Global Search (Part(None, ...)),
we ensure compatibility across different KiCad library versions on Streamlit.
"""

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    AMS1117-3.3 Wiring: 1=GND, 2=OUT, 3=IN.
    """
    v33 = Net('3V3')
    
    # Instantiate using Global Search to find 'AMS1117-3.3' in any loaded library
    reg = Part(None, 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part(None, 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part(None, 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Robust wiring using pin indices to avoid naming conflicts
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32.
    Uses 'Global Hunter' logic to find symbols without hardcoded library names.
    """
    mcu = None
    # Patterns to search for in order of preference
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-WROOM-32', 'ESP32-S3']
    
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results:
                # results is a list of part names; we try to instantiate the first match
                target_part = results[0]
                mcu = Part(None, target_part, footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                if mcu:
                    logger.info(f"Modular Discovery matched MCU: {target_part}")
                    break
        except:
            continue

    if not mcu:
        # FALLBACK: Handle legacy KiCad naming for connectors if ESP32 is missing
        logger.warning("ESP32 symbols missing. Attempting legacy Connector fallback.")
        fallback_names = ['Conn_01x19', 'Conn_01x20', 'Connector_Generic:Conn_01x19']
        for fb in fallback_names:
            try:
                mcu = Part(None, fb, footprint='Connector_PinHeader_2.54mm:PinHeader_1x19_P2.54mm_Vertical')
                if mcu: break
            except: continue

    # Supporting Decoupling Capacitor
    c_dec = Part(None, 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # --- HEURISTIC WIRING ---
    # Power (3.3V) - Usually Pin 2 on most modules
    p_3v3_bound = False
    for p_name in ['3V3', 'VDD', 'VCC', '3.3V', '1']:
        try:
            if mcu[p_name] is not None:
                mcu[p_name] += v33_net
                p_3v3_bound = True
                break
        except: continue
    if not p_3v3_bound: mcu[2] += v33_net 

    # Ground - Usually Pin 1 or 38
    try: mcu['GND'] += gnd_net
    except: mcu[1] += gnd_net 
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # Enable (EN) Pull-up - Usually Pin 3
    r_en = Part(None, 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1]
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Macro: 4.7k Pull-up resistors for the I2C Bus."""
    r_sda = Part(None, 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part(None, 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    
    sda_net += r_sda[1]
    scl_net += r_scl[1]
    r_sda[2] += vcc_net
    r_scl[2] += vcc_net
    
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="RED"):
    """Macro: LED with current limiting resistor."""
    led = Part(None, 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part(None, 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    
    signal_net += res[1]
    res[2]     += led[1] # Anode
    led[2]     += gnd_net # Cathode
    
    return led, res
