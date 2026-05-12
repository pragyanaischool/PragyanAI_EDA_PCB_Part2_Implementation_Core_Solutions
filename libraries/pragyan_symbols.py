import sys
import os
import logging
from skidl import Part, Net, search, KICAD, Pin

# --- 1. PATH STABILIZATION ---
# Ensures the root directory is accessible for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logger = logging.getLogger("PragyanAI-Symbols")

def _get_pin_safely(part, identifiers):
    """
    Core Utility: Attempts to locate a pin by name or physical index.
    Crucial for bridging named MCU symbols to numbered generic connectors.
    """
    for identifier in identifiers:
        try:
            # SKiDL allows accessing pins by string names or integer indices
            pin = part[identifier]
            if pin is not None:
                return pin
        except (KeyError, IndexError, AttributeError, TypeError):
            continue
    return None

def PowerStage_LDO_3V3(vin_net, gnd_net):
    v33 = Net('3V3')
    
    # --- 1. ROBUST REGULATOR LOAD ---
    reg = None
    try:
        # Attempt to find the specific part first
        reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    except:
        # CRITICAL FALLBACK: Define the part manually if the library is missing
        reg = Part(name='AMS1117_3V3', dest=KICAD, pins=[
            Pin(num='1', name='GND'), Pin(num='2', name='VOUT'), Pin(num='3', name='VIN')
        ])
        reg.footprint = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'

    # --- 2. ROBUST PASSIVE LOAD (FIXES LINE 45) ---
    # Manually defining pins ensures the 'Part' is never empty
    c_in = Part(name='C_10uF', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='10uF')
    c_in.footprint = 'Capacitor_SMD:C_0603_1608Metric'

    c_out = Part(name='C_22uF', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='22uF')
    c_out.footprint = 'Capacitor_SMD:C_0603_1608Metric'

    # Mapping logic using variables (Safe assignment)
    p_vin = _get_pin_safely(reg, [3, '3', 'VIN'])
    if p_vin: p_vin += vin_net
    
    p_gnd = _get_pin_safely(reg, [1, '1', 'GND'])
    if p_gnd: p_gnd += gnd_net
    
    p_vout = _get_pin_safely(reg, [2, '2', 'VOUT'])
    if p_vout: p_vout += v33

    # Wire the capacitors
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

from skidl import Part, Net, search, KICAD, Pin

def ESP32_Minimal_System(v33_net, gnd_net):
    mcu = None
    # Try discovery...
    try:
        results = search('ESP32-S3')
        if results:
            mcu = Part(None, results[0], footprint='RF_Module:ESP32-S3-WROOM-1-N8')
    except: pass

    # Fallback to dynamic definition
    if mcu is None:
        mcu = Part(name='ESP32_CORE_GENERIC', dest=KICAD, pins=[Pin(num=str(i)) for i in range(1, 21)])
        mcu.footprint = 'Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical'

    # Manually define pull-up resistor (Safe against missing libraries)
    r_en = Part(name='R_10k', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='10k')
    r_en.footprint = 'Resistor_SMD:R_0603_1608Metric'

    # Mapping
    p_vcc = _get_pin_safely(mcu, ['3V3', 'VCC', 2])
    if p_vcc: p_vcc += v33_net
    
    p_en = _get_pin_safely(mcu, ['EN', 3])
    if p_en: p_en += r_en[1]
    r_en[2] += v33_net

    return mcu

def I2C_Pullups(sda_net, scl_net, vcc_net):
    """Macro: 4.7k Pull-up resistors for the I2C Bus."""
    r_sda = Part(name='R_SDA', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='4.7k')
    r_scl = Part(name='R_SCL', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='4.7k')
    r_sda.footprint = 'Resistor_SMD:R_0603_1608Metric'
    r_scl.footprint = 'Resistor_SMD:R_0603_1608Metric'
    
    sda_net += r_sda[1]; scl_net += r_scl[1]
    r_sda[2] += vcc_net; r_scl[2] += vcc_net
    return r_sda, r_scl

def Status_LED(signal_net, gnd_net, color="GREEN"):
    """Macro: Visual Power indicator LED."""
    led = Part(name='LED_PWR', dest=KICAD, pins=[Pin(num='1', name='K'), Pin(num='2', name='A')])
    res = Part(name='R_LED', dest=KICAD, pins=[Pin(num='1'), Pin(num='2')], value='330')
    led.footprint = 'LED_SMD:LED_0603_1608Metric'
    res.footprint = 'Resistor_SMD:R_0603_1608Metric'
    
    res[1] += signal_net
    res[2] += led[2] # Anode
    led[1] += gnd_net # Cathode
    return led, res
    
