import sys
import os
import logging
from skidl import Part, Net, search, KICAD, Pin

# --- 1. PATH STABILIZATION ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

def _get_pin_safely(part, identifiers):
    """
    Core Utility: Attempts to locate a pin by name or physical index.
    Crucial for bridging the gap between named MCU symbols and numbered connectors.
    """
    for identifier in identifiers:
        try:
            # SKiDL allows accessing pins by string names or integer indices
            pin = part[identifier]
            if pin is not None:
                return pin
        except:
            continue
    return None

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage.
    AMS1117-3.3: 1=GND, 2=VOUT, 3=VIN.
    """
    v33 = Net('3V3')
    
    # Discovery with indexing fallback
    reg = None
    try:
        results = search('AMS1117-3.3')
        if results:
            reg = Part(None, results[0], footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    except: pass

    if reg is None:
        # Fallback to dynamic 3-pin regulator
        reg = Part(name='AMS1117_REG', dest=KICAD, pins=[
            Pin(num='1', name='GND'), Pin(num='2', name='VOUT'), Pin(num='3', name='VIN')
        ])
        reg.footprint = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'

    # Map Pins by Index (Standard for SOT-223)
    # index 3 = IN, index 1 = GND, index 2 = OUT
    _get_pin_safely(reg, [3, '3', 'VIN']) += vin_net
    _get_pin_safely(reg, [1, '1', 'GND']) += gnd_net
    _get_pin_safely(reg, [2, '2', 'VOUT', 'VOUT/ADJ']) += v33
    
    # Supporting Capacitors
    try:
        c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
        c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    except:
        c_in = Part(name='C_IN', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], footprint='Capacitor_SMD:C_0603_1608Metric')
        c_out = Part(name='C_OUT', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], footprint='Capacitor_SMD:C_0603_1608Metric')

    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32.
    Uses physical pin fallbacks to handle generic 20-pin connector symbols.
    """
    mcu = None
    search_patterns = ['ESP32-S3-WROOM-1', 'ESP32-WROOM-32', 'ESP32-S3']
    
    for pattern in search_patterns:
        try:
            results = search(pattern)
            if results:
                mcu = Part(None, results[0], footprint='RF_Module:ESP32-S3-WROOM-1-N8')
                if mcu: break
        except: continue

    if mcu is None:
        logger.warning("Falling back to Dynamic 20-pin Part Definition.")
        # Create a generic 20-pin part if libraries aren't indexed
        mcu = Part(name='ESP32_CORE_J3', dest=KICAD, pins=[Pin(num=str(i)) for i in range(1, 21)])
        mcu.footprint = 'Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical'

    # --- ROBUST HEURISTIC WIRING ---
    
    # 1. Power Rail (Usually Pin 2 on dev boards/headers)
    p_vcc = _get_pin_safely(mcu, ['3V3', 'VDD', 'VCC', 2, '2'])
    if p_vcc: p_vcc += v33_net

    # 2. Ground Rail (Usually Pin 1)
    p_gnd = _get_pin_safely(mcu, ['GND', 1, '1', 38, '38'])
    if p_gnd: p_gnd += gnd_net

    # 3. Enable Pull-up (Usually Pin 3)
    p_en = _get_pin_safely(mcu, ['EN', 'CH_PD', 3, '3'])
    if p_en:
        r_en = Part(name='R_EN', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='10k')
        r_en.footprint = 'Resistor_SMD:R_0603_1608Metric'
        p_en += r_en[1]
        r_en[2] += v33_net

    # Decoupling
    c_dec = Part(name='C_DEC', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='0.1uF')
    c_dec.footprint = 'Capacitor_SMD:C_0603_1608Metric'
    c_dec[1, 2] += v33_net, gnd_net
    
    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Standard I2C Pull-up macro."""
    # Using generic Part definition for maximum stability
    r_sda = Part(name='R_SDA', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='4.7k')
    r_scl = Part(name='R_SCL', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='4.7k')
    r_sda.footprint = 'Resistor_SMD:R_0603_1608Metric'
    r_scl.footprint = 'Resistor_SMD:R_0603_1608Metric'
    
    sda_net += r_sda[1]; scl_net += r_scl[1]
    r_sda[2] += vcc_net; r_scl[2] += vcc_net
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="GREEN"):
    """Generic LED Macro."""
    led = Part(name='LED_PWR', dest=KICAD, pins=[Pin(num='1', name='K'), Pin(num='2', name='A')])
    res = Part(name='R_LED', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='330')
    led.footprint = 'LED_SMD:LED_0603_1608Metric'
    res.footprint = 'Resistor_SMD:R_0603_1608Metric'
    
    signal_net += res[1]
    res[2]     += led[2] # Anode
    led[1]     += gnd_net # Cathode
    return led, res
