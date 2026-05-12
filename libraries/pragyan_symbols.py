import sys
import os
import logging

from skidl import (
    Part,
    Net,
    search,
    KICAD,
    Pin,
    lib_search_paths
)

# =========================================================
# PATH STABILIZATION
# =========================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..')
    )
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("PragyanAI-Symbols")

# =========================================================
# KICAD LIBRARY PATH
# =========================================================

try:
    lib_search_paths[KICAD].append(
        "/usr/share/kicad/symbols"
    )

    print("[SKIDL] KiCad library path added.")

except Exception as e:

    print(
        f"[WARNING] Could not configure "
        f"KiCad libraries: {e}"
    )

# =========================================================
# SAFE PIN ACCESSOR
# =========================================================

def _get_pin_safely(part, identifiers):
    """
    Safely find a pin by:
    - number
    - name
    """

    for identifier in identifiers:

        try:

            pin = part[identifier]

            if pin is not None:
                return pin

        except (
            KeyError,
            IndexError,
            AttributeError,
            TypeError
        ):
            continue

    return None

# =========================================================
# SAFE PART CREATOR
# =========================================================

def safe_part(
    library=None,
    symbol=None,
    name=None,
    value=None,
    footprint=None,
    pins=None
):
    """
    Ultra-safe SKiDL part generator.

    Handles:
    - library parts
    - generic parts
    - missing libraries
    - invalid definitions
    """

    try:

        print(
            f"[DEBUG] safe_part("
            f"library={library}, "
            f"symbol={symbol}, "
            f"name={name})"
        )

        # =====================================================
        # LIBRARY PART
        # =====================================================

        if library and symbol:

            logger.info(
                f"Creating library part: "
                f"{library}:{symbol}"
            )

            p = Part(
                library,
                symbol,
                footprint=footprint
            )

        # =====================================================
        # GENERIC PART
        # =====================================================

        else:

            # -----------------------------------------
            # SAFE DEFAULT NAME
            # -----------------------------------------

            if not name:

                logger.warning(
                    "No part name provided. "
                    "Using GENERIC_PART."
                )

                name = "GENERIC_PART"

            # -----------------------------------------
            # SAFE DEFAULT PINS
            # -----------------------------------------

            if not pins:

                logger.warning(
                    f"No pins supplied for "
                    f"{name}. "
                    f"Creating default 2-pin device."
                )

                pins = [
                    Pin(num='1'),
                    Pin(num='2')
                ]

            logger.info(
                f"Creating generic part: {name}"
            )

            p = Part(
                name=name,
                dest=KICAD,
                pins=pins
            )

            # -----------------------------------------
            # FOOTPRINT
            # -----------------------------------------

            if footprint:
                p.footprint = footprint

        # =====================================================
        # OPTIONAL VALUE
        # =====================================================

        if value:
            p.value = value

        return p

    except Exception as e:

        logger.error(
            f"Failed to create part: "
            f"{library}:{symbol} -> {e}"
        )

        raise RuntimeError(
            f"Part creation failed: {e}"
        )

# =========================================================
# POWER STAGE
# =========================================================

def PowerStage_LDO_3V3(
    vin_net,
    gnd_net
):

    v33 = Net('3V3')

    # -----------------------------------------------------
    # AMS1117 REGULATOR
    # -----------------------------------------------------

    try:

        reg = safe_part(
            library='Regulator_Linear',
            symbol='AMS1117-3.3',
            footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2'
        )

        print(
            "[SKIDL] Loaded AMS1117 "
            "from KiCad library."
        )

    except Exception as e:

        print(
            f"[WARNING] AMS1117 load failed: {e}"
        )

        reg = safe_part(
            name='AMS1117_3V3',
            footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2',
            pins=[
                Pin(num='1', name='GND'),
                Pin(num='2', name='VOUT'),
                Pin(num='3', name='VIN')
            ]
        )

    # -----------------------------------------------------
    # INPUT CAP
    # -----------------------------------------------------

    c_in = safe_part(
        name='C_10uF',
        value='10uF',
        footprint='Capacitor_SMD:C_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    # -----------------------------------------------------
    # OUTPUT CAP
    # -----------------------------------------------------

    c_out = safe_part(
        name='C_22uF',
        value='22uF',
        footprint='Capacitor_SMD:C_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    # -----------------------------------------------------
    # CONNECTIONS
    # -----------------------------------------------------

    p_vin = _get_pin_safely(
        reg,
        [3, '3', 'VIN']
    )

    if p_vin:
        p_vin += vin_net

    p_gnd = _get_pin_safely(
        reg,
        [1, '1', 'GND']
    )

    if p_gnd:
        p_gnd += gnd_net

    p_vout = _get_pin_safely(
        reg,
        [2, '2', 'VOUT']
    )

    if p_vout:
        p_vout += v33

    # -----------------------------------------------------
    # CAPACITOR WIRING
    # -----------------------------------------------------

    c_in[1] += vin_net
    c_in[2] += gnd_net

    c_out[1] += v33
    c_out[2] += gnd_net

    return v33, reg

# =========================================================
# ESP32 MINIMAL SYSTEM
# =========================================================

def ESP32_Minimal_System(
    v33_net,
    gnd_net
):

    mcu = None

    # -----------------------------------------------------
    # TRY REAL ESP32 SYMBOL
    # -----------------------------------------------------

    try:

        mcu = safe_part(
            library="RF_Module",
            symbol="ESP32-S3-WROOM-1",
            footprint="RF_Module:ESP32-S3-WROOM-1"
        )

        print(
            "[SKIDL] ESP32 loaded "
            "from library."
        )

    except Exception as e:

        print(
            f"[WARNING] ESP32 load failed: {e}"
        )

        # -------------------------------------------------
        # FALLBACK GENERIC MCU
        # -------------------------------------------------

        mcu = safe_part(
            name='ESP32_CORE_GENERIC',
            footprint=(
                'Connector_PinHeader_2.54mm:'
                'PinHeader_2x20_P2.54mm_Vertical'
            ),
            pins=[
                Pin(
                    num=str(i),
                    name=f"GPIO{i}"
                )
                for i in range(1, 41)
            ]
        )

    # -----------------------------------------------------
    # ENABLE RESISTOR
    # -----------------------------------------------------

    r_en = safe_part(
        name='R_10K',
        value='10k',
        footprint='Resistor_SMD:R_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    # -----------------------------------------------------
    # POWER
    # -----------------------------------------------------

    p_vcc = _get_pin_safely(
        mcu,
        ['3V3', 'VCC', 'VIN', 2]
    )

    if p_vcc:
        p_vcc += v33_net
    else:
        print(
            "[WARNING] ESP32 VCC "
            "pin not found."
        )

    # -----------------------------------------------------
    # GROUND
    # -----------------------------------------------------

    p_gnd = _get_pin_safely(
        mcu,
        ['GND', 1]
    )

    if p_gnd:
        p_gnd += gnd_net
    else:
        print(
            "[WARNING] ESP32 GND "
            "pin not found."
        )

    # -----------------------------------------------------
    # ENABLE PIN
    # -----------------------------------------------------

    p_en = _get_pin_safely(
        mcu,
        ['EN', 'CHIP_EN', 3]
    )

    if p_en:

        p_en += r_en[1]
        r_en[2] += v33_net

    else:

        print(
            "[WARNING] ESP32 EN "
            "pin not found."
        )

    return mcu

# =========================================================
# I2C PULLUPS
# =========================================================

def I2C_Pullups(
    sda_net,
    scl_net,
    vcc_net
):

    r_sda = safe_part(
        name='R_SDA',
        value='4.7k',
        footprint='Resistor_SMD:R_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    r_scl = safe_part(
        name='R_SCL',
        value='4.7k',
        footprint='Resistor_SMD:R_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    r_sda[1] += sda_net
    r_sda[2] += vcc_net

    r_scl[1] += scl_net
    r_scl[2] += vcc_net

    return r_sda, r_scl

# =========================================================
# STATUS LED
# =========================================================

def Status_LED(
    signal_net,
    gnd_net,
    color="GREEN"
):

    led = safe_part(
        name='LED_PWR',
        footprint='LED_SMD:LED_0603_1608Metric',
        pins=[
            Pin(num='1', name='K'),
            Pin(num='2', name='A')
        ]
    )

    res = safe_part(
        name='R_LED',
        value='330',
        footprint='Resistor_SMD:R_0603_1608Metric',
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )

    # -----------------------------------------------------
    # CONNECTIONS
    # -----------------------------------------------------

    res[1] += signal_net

    res[2] += led[2]

    led[1] += gnd_net

    return led, res

# =========================================================
# DEFAULT GENERIC 2-PIN DEVICE
# =========================================================

def default_two_pin(
    name="GENERIC_2PIN"
):

    return safe_part(
        name=name,
        pins=[
            Pin(num='1'),
            Pin(num='2')
        ]
    )
    
