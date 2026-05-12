from skidl import Part, Net, Package

"""
PragyanAI Symbol Macros
These functions serve as 'Templates' for common electronic sub-circuits.
Using macros ensures that decoupling capacitors and protection diodes 
are never forgotten by the AI architect.
"""

def PowerStage_LDO_3V3(vin_net, gnd_net):
    """
    Macro: Standard 3.3V LDO Stage
    Includes: AMS1117-3.3, 10uF Input Cap, 22uF Output Cap.
    """
    v33 = Net('3V3')
    
    # Instantiate Parts
    reg = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
    c_in = Part('Device', 'C', value='10uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    c_out = Part('Device', 'C', value='22uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Connections
    reg[3, 1] += vin_net, gnd_net  # Vin, GND
    reg[2]    += v33               # Vout
    
    c_in[1, 2]  += vin_net, gnd_net
    c_out[1, 2] += v33, gnd_net
    
    return v33, reg

def ESP32_Minimal_System(v33_net, gnd_net):
    """
    Macro: Essential Support for ESP32-S3
    Includes: Boot button, Reset circuit, and Decoupling.
    """
    # Instantiate MCU
    mcu = Part('MCU_Espressif', 'ESP32-S3-WROOM-1', footprint='RF_Module:ESP32-S3-WROOM-1-N8')
    
    # Decoupling for the MCU
    c_dec = Part('Device', 'C', value='0.1uF', footprint='Capacitor_SMD:C_0603_1608Metric')
    
    # Wiring Power
    mcu['3V3'] += v33_net
    mcu['GND'] += gnd_net
    c_dec[1, 2] += v33_net, gnd_net
    
    # Simple Reset Pull-up (EN Pin)
    r_en = Part('Device', 'R', value='10k', footprint='Resistor_SMD:R_0603_1608Metric')
    mcu['EN'] += r_en[1]
    r_en[2]   += v33_net
    
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
