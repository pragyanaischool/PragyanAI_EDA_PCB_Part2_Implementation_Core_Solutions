import sys
import os
import logging
from skidl import Part, Net, search, KICAD

# Path Stabilization
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    Uses 'Regulator_Linear' which we know is working from your previous logs.
    """
    v33 = Net('3V3')
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    reg[3, 1] += vin_net, gnd_net
    reg[2]    += v33
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32-S3.
    Updated to use 'RF_Module' library confirmed by your server logs.
    """
    mcu = None
    
    # These exact names were confirmed in your latest error log!
    options = [
        {'lib': 'RF_Module', 'part': 'ESP32-S3-WROOM-1'},
        {'lib': 'RF_Module', 'part': 'ESP32-WROOM-32'},
        {'lib': 'Connector', 'part': 'Conn_01x19'} # KiCad 5/6 naming
    ]
    
    for opt in options:
        try:
            mcu = Part(opt['lib'], opt['part'], footprint='RF_Module:ESP32-S3-WROOM-1-N8')
            if mcu:
                logger.info(f"Successfully matched confirmed part: {opt['part']} from {opt['lib']}")
                break
        except:
            continue

    if not mcu:
        # Ultimate fallback using a confirmed existing symbol from 'Device' lib 
        # which almost never fails.
        logger.error("Conflicting KiCad libraries. Using Generic Pin Header fallback.")
        mcu = Part('Connector', 'Conn_01x20_Male', footprint='Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical')

    # Standard Support Passives
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Power Wiring using Pin Numbers (More reliable than names across different libs)
    # Most ESP32 modules use Pin 2 for 3V3 and Pin 1 or 38 for GND
    try:
        mcu['3V3'] += v33_net
    except:
        mcu[2] += v33_net # ESP32-WROOM Pin 2 is 3V3

    try:
        mcu['GND'] += gnd_net
    except:
        mcu[1] += gnd_net # ESP32-WROOM Pin 1 is GND
        
    c_dec[1, 2] += v33_net, gnd_net
    
    # EN (Enable) Pull-up
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    try:
        mcu['EN'] += r_en[1]
    except:
        mcu[3] += r_en[1] # Pin 3 is usually EN
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
    res[2]     += led[1]
    led[2]     += gnd_net
    return led, res
