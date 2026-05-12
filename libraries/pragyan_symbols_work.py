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
    AMS1117-3.3 standard pinout: 1=GND, 2=VOUT, 3=VIN.
    """
    v33 = Net('3V3')
    
    # 1. Attempt to find the LDO in any loaded library
    reg_results = search('AMS1117-3.3')
    if reg_results:
        reg = Part(None, reg_results[0], footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    else:
        # Fallback to explicit library name if global search isn't indexed yet
        reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
        
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring by index (Robust against naming drift)
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32.
    Validates search results to prevent "Empty Part" crashes.
    """
    mcu = None
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-WROOM-32', 'ESP32-S3']
    
    # 2. Heuristic Discovery Logic
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results and len(results) > 0:
                # We found a match! Instantiate using the first result.
                mcu = Part(None, results[0], footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                if mcu:
                    logger.info(f"Implementation Core successfully instantiated: {results[0]}")
                    break
        except:
            continue

    # 3. CRITICAL FAIL-SAFE: If search returns nothing, we MUST provide a fallback
    # Passing None to Part() is what causes the crash. We prevent that here.
    if mcu is None:
        logger.warning("Global MCU search failed. Using 20-pin header fallback.")
        # This fallback uses a generic connector likely to be in standard libraries
        mcu = Part('Connector', 'Conn_01x20', footprint='Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical')

    # Supporting Passives
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Heuristic Power Wiring (Try Name -> Try Index)
    p_3v3_bound = False
    for p_name in ['3V3', 'VDD', 'VCC', '3.3V', '1']:
        try:
            if mcu[p_name] is not None:
                mcu[p_name] += v33_net
                p_3v3_bound = True
                break
        except: continue
    if not p_3v3_bound: mcu[2] += v33_net 

    # Ground Wiring
    try: mcu['GND'] += gnd_net
    except: mcu[1] += gnd_net 
    
    c_dec[1, 2] += v33_net, gnd_net
    
    # Enable Logic
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try: mcu['EN'] += r_en[1]
    except: mcu[3] += r_en[1]
    r_en[2] += v33_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Macro: 4.7k Pull-up resistors for the I2C Bus."""
    r_sda = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    r_scl = Part('Device', 'R', value='4.7k', footprint='Resistor_SMD:R_0603_1608Metric')
    sda_net += r_sda[1]; scl_net += r_scl[1]
    r_sda[2] += vcc_net; r_scl[2] += vcc_net
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="GREEN"):
    """Macro: Status indication LED."""
    led = Part('Device', 'LED', footprint='LED_SMD:LED_0603_1608Metric')
    res = Part('Device', 'R', value='330', footprint='Resistor_SMD:R_0603_1608Metric')
    signal_net += res[1]; res[2] += led[1]; led[2] += gnd_net
    return led, res
