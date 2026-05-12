import sys
import os
import logging
from skidl import Part, Net, search, KICAD

# --- PATH STABILIZATION ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

"""
PragyanAI Symbol Macros: Global Search Edition
Designed for high-resilience deployment on Streamlit Cloud.
Uses index-based fallback for wiring to handle varied pin naming.
"""

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    AMS1117-3.3 standard pinout: 1=GND, 2=VOUT, 3=VIN.
    """
    v33 = Net('3V3')
    
    # Global search for the AMS1117-3.3 part
    reg = Part(None, 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part(None, 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part(None, 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring by index is safer than wiring by name in cloud environments
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32.
    Uses 'Global Hunter' logic to find parts without hardcoded library names.
    """
    mcu = None
    # Prioritized patterns for ESP32 discovery
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-WROOM-32', 'ESP32-S3']
    
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results:
                # results is a list of part names; use the first match
                target_part = results[0]
                mcu = Part(None, target_part, footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                if mcu:
                    logger.info(f"Implementation Core matched MCU: {target_part}")
                    break
        except:
            continue

    if not mcu:
        # FAIL-SAFE: If specific ESP32 symbols aren't found, use a legacy connector
        logger.warning("ESP32 symbols missing. Attempting legacy Connector fallback.")
        fallback_names = ['Conn_01x19', 'Conn_01x20', 'Conn_01x19_Male']
        for fb in fallback_names:
            try:
                mcu = Part(None, fb, footprint='Connector_PinHeader_2.54mm:PinHeader_1x19_P2.54mm_Vertical')
                if mcu: break
            except: continue

    # Decoupling for stability
    c_dec = Part(None, 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # --- HEURISTIC POWER BINDING ---
    p_3v3_bound = False
    # Try common names for 3.3V power
    for p_name in ['3V3', 'VDD', 'VCC', '3.3V']:
        try:
            if mcu[p_name] is not None:
                mcu[p_name] += v33_net
                p_3v3_bound = True
                break
        except: continue
    # Fallback to physical Pin 2 if name-based mapping fails
    if not p_3v3_bound: mcu[2] += v33_net 

    # Ground (Usually Pin 1 or 38)
    try: mcu['GND'] += gnd_net
    except: mcu[1] += gnd_net 
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # EN (Enable) Pull-up - Critical for ESP32 startup
    r_en = Part(None, 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1] # Pin 3 is standard EN index
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

def Status_LED(signal_net, gnd_net, color="GREEN"):
    """Macro: Power/Status indicator LED."""
    led = Part(None, 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part(None, 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    
    signal_net += res[1]
    res[2]     += led[1] # Anode
    led[2]     += gnd_net # Cathode
    
    return led, res
