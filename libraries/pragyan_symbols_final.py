import sys
import os
import logging
from skidl import Part, Net, search, KICAD, Pin

# --- 1. PATH STABILIZATION ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    Attempts to find AMS1117-3.3, with a generic fallback.
    """
    v33 = Net('3V3')
    
    # Attempt to discover the LDO via fuzzy search
    reg_results = search('AMS1117-3.3')
    if reg_results:
        reg = Part(None, reg_results[0], footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    else:
        # Emergency Fallback: If libraries are not yet indexed, use explicit name
        try:
            reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
        except:
            # Last Resort: Dynamic 3-pin part definition
            reg = Part(name='AMS1117_FIXED', dest=KICAD, pins=[Pin(num='1', name='GND'), Pin(num='2', name='VOUT'), Pin(num='3', name='VIN')])
            reg.footprint = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'

    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Robust wiring using pin indices
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32.
    Implements Dynamic Part Definition if KiCad libraries are missing/unindexed.
    """
    mcu = None
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-WROOM-32', 'ESP32-S3']
    
    # 1. Attempt Fuzzy Discovery
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results and len(results) > 0:
                mcu = Part(None, results[0], footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                if mcu: break
        except: continue

    # 2. Attempt Explicit Connector Fallback (trying common library naming variations)
    if mcu is None:
        logger.warning("MCU symbols missing. Checking Connector variations...")
        for lib in ['Connector', 'Connector_Generic', 'conn']:
            try:
                # Trying standard 20-pin header as proxy for ESP32 breakout
                mcu = Part(lib, 'Conn_01x20', footprint='Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical')
                if mcu: break
            except: continue

    # 3. ULTIMATE FIX: Create the Part on-the-fly if libraries are totally absent
    if mcu is None:
        logger.error("No hardware libraries found on server. Generating dynamic component.")
        mcu = Part(name='ESP32_S3_CORE', dest=KICAD, pins=[Pin(num=str(i)) for i in range(1, 21)])
        mcu.footprint = 'Connector_PinHeader_2.54mm:PinHeader_1x19_P2.54mm_Vertical'

    # Supporting Passives (Hardcoded to 'Device' lib)
    try:
        c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    except:
        c_dec = Part(name='C_FIXED', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')])

    # Heuristic Wiring (Attempt by Name, Fallback to Physical Pin)
    p_3v3_bound = False
    for p_name in ['3V3', 'VDD', 'VCC', '3.3V', '1']:
        try:
            if mcu[p_name] is not None:
                mcu[p_name] += v33_net
                p_3v3_bound = True
                break
        except: continue
    if not p_3v3_bound: mcu[2] += v33_net 

    try: mcu['GND'] += gnd_net
    except: mcu[1] += gnd_net 
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # Enable Logic Pull-up
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1]
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    r_sda = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    sda_net += r_sda[1]; scl_net += r_scl[1]
    r_sda[2] += vcc_net; r_scl[2] += vcc_net
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="GREEN"):
    led = Part('Device', 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part('Device', 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    signal_net += res[1]; res[2] += led[1]; led[2] += gnd_net
    return led, res
