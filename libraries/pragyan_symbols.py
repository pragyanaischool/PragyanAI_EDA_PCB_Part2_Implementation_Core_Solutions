import sys
import os
import logging
from skidl import Part, Net, search, KICAD

# --- 1. PATH STABILIZATION ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    AMS1117-3.3 Wiring: 1=GND, 2=OUT/TAB, 3=IN
    """
    v33 = Net('3V3')
    
    # Using standard 'Regulator_Linear' confirmed to be present on the server
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Robust wiring using indices (1, 2, 3) to bypass pin-name mismatch
    reg[3] += vin_net
    reg[2] += v33
    reg[1] += gnd_net
    
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32-S3.
    Uses 'Global Hunter' discovery logic with explicit pin-index fallback.
    """
    mcu = None
    # Priority patterns for ESP32 discovery
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-S3', 'ESP32-WROOM-32']
    
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results:
                target_part = results[0]
                # Target 'RF_Module' or 'MCU_Espressif'
                for lib_name in ['RF_Module', 'MCU_Espressif']:
                    try:
                        mcu = Part(lib_name, target_part, footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                        if mcu: break
                    except: continue
            if mcu: 
                logger.info(f"Symbol Discovery Success: {mcu.lib}:{mcu.name}")
                break
        except: continue

    if not mcu:
        # FAIL-SAFE: Generic Connector (Standard ESP32 modules use 38 pins)
        logger.warning("No ESP32 symbols found. Using Generic Header fallback.")
        mcu = Part('Connector', 'Conn_01x19_Male', footprint='Connector_PinHeader_2.54mm:PinHeader_1x19_P2.54mm_Vertical')

    # Standard Supporting Passives
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # --- ROBUST WIRING LOGIC ---
    # Attempt by Name, Fallback to Physical Pin Number (ESP32-S3 Standard)
    
    # 3.3V Power (Usually Pin 2)
    p_3v3_bound = False
    for p_name in ['3V3', 'VDD', 'VCC', '3.3V']:
        try:
            if mcu[p_name] is not None:
                mcu[p_name] += v33_net
                p_3v3_bound = True
                break
        except: continue
    if not p_3v3_bound: mcu[2] += v33_net 

    # GND (Usually Pin 1 or Pin 38)
    try: mcu['GND'] += gnd_net
    except: mcu[1] += gnd_net 
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # EN (Enable) Pull-up (Usually Pin 3)
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1]
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    r_sda = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    sda_net += r_sda[1]
    scl_net += r_scl[1]
    r_sda[2] += vcc_net
    r_scl[2] += vcc_net
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="RED"):
    led = Part('Device', 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part('Device', 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    signal_net += res[1]
    res[2] += led[1]
    led[2] += gnd_net
    return led, res
