import sys
import os
import uuid
import logging

from skidl import (
    Part,
    Net,
    KICAD,
    lib_search_paths
)

# =========================================================
# PATH STABILIZATION
# =========================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("PragyanAI-Symbols")

# =========================================================
# KICAD LIBRARY CONFIG
# =========================================================

try:

    lib_search_paths[KICAD].append(
        "/usr/share/kicad/symbols"
    )

    print("[SKIDL] KiCad library path added.")

except Exception as e:

    print(
        f"[WARNING] Could not configure "
        f"KiCad library path: {e}"
    )

# =========================================================
# SAFE PIN ACCESS
# =========================================================

def _get_pin_safely(part, identifiers):

    for identifier in identifiers:

        try:

            pin = part[identifier]

            if pin is not None:
                return pin

        except Exception:
            continue

    return None

# =========================================================
# GPIO HELPER
# =========================================================

def get_gpio_pin(part, gpio_num):
    """
    Universal GPIO resolver for ESP32 symbols.
    Handles:
    GPIO1
    IO1
    1
    """

    candidates = [
        f"GPIO{gpio_num}",
        f"IO{gpio_num}",
        str(gpio_num)
    ]

    return _get_pin_safely(
        part,
        candidates
    )

# =========================================================
# SAFE PART CREATOR
# =========================================================

def safe_part(
    library=None,
    symbol=None,
    value=None,
    footprint=None
):

    try:

        print(
            f"[DEBUG] "
            f"library={library}, "
            f"symbol={symbol}"
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not library:
            raise ValueError(
                "Missing library name."
            )

        if not symbol:
            raise ValueError(
                "Missing symbol name."
            )

        # -------------------------------------------------
        # CREATE PART
        # -------------------------------------------------

        p = Part(
            library,
            symbol,
            footprint=footprint,
            tag=str(uuid.uuid4())[:8]
        )

        # -------------------------------------------------
        # OPTIONAL VALUE
        # -------------------------------------------------

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

    reg = safe_part(
        library='Regulator_Linear',
        symbol='AMS1117-3.3',
        footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2'
    )

    print(
        "[SKIDL] Loaded AMS1117 "
        "from library."
    )

    # -----------------------------------------------------
    # INPUT CAPACITOR
    # -----------------------------------------------------

    c_in = safe_part(
        library='Device',
        symbol='C',
        value='10uF',
        footprint='Capacitor_SMD:C_0603_1608Metric'
    )

    # -----------------------------------------------------
    # OUTPUT CAPACITOR
    # -----------------------------------------------------

    c_out = safe_part(
        library='Device',
        symbol='C',
        value='22uF',
        footprint='Capacitor_SMD:C_0603_1608Metric'
    )

    # -----------------------------------------------------
    # REGULATOR PINS
    # -----------------------------------------------------

    p_vin = _get_pin_safely(
        reg,
        [3, '3', 'VIN']
    )

    if p_vin:
        p_vin += vin_net
    else:
        print("[WARNING] VIN pin not found.")

    p_gnd = _get_pin_safely(
        reg,
        [1, '1', 'GND']
    )

    if p_gnd:
        p_gnd += gnd_net
    else:
        print("[WARNING] GND pin not found.")

    p_vout = _get_pin_safely(
        reg,
        [2, '2', 'VOUT']
    )

    if p_vout:
        p_vout += v33
    else:
        print("[WARNING] VOUT pin not found.")

    # -----------------------------------------------------
    # CAP CONNECTIONS
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

    # -----------------------------------------------------
    # ESP32 MODULE
    # -----------------------------------------------------

    mcu = safe_part(
        library="RF_Module",
        symbol="ESP32-S3-WROOM-1",
        footprint="RF_Module:ESP32-S3-WROOM-1"
    )

    print(
        "[SKIDL] ESP32 loaded "
        "from library."
    )

    # -----------------------------------------------------
    # ENABLE RESISTOR
    # -----------------------------------------------------

    r_en = safe_part(
        library='Device',
        symbol='R',
        value='10k',
        footprint='Resistor_SMD:R_0603_1608Metric'
    )

    # -----------------------------------------------------
    # POWER PIN
    # -----------------------------------------------------

    p_vcc = _get_pin_safely(
        mcu,
        ['3V3', 'VCC', 'VIN']
    )

    if p_vcc:
        p_vcc += v33_net
    else:
        print(
            "[WARNING] ESP32 power "
            "pin not found."
        )

    # -----------------------------------------------------
    # GROUND PIN
    # -----------------------------------------------------

    p_gnd = _get_pin_safely(
        mcu,
        ['GND']
    )

    if p_gnd:
        p_gnd += gnd_net
    else:
        print(
            "[WARNING] ESP32 ground "
            "pin not found."
        )

    # -----------------------------------------------------
    # ENABLE PIN
    # -----------------------------------------------------

    p_en = _get_pin_safely(
        mcu,
        ['EN', 'CHIP_EN']
    )

    if p_en:

        p_en += r_en[1]

        r_en[2] += v33_net

    else:

        print(
            "[WARNING] ESP32 EN "
            "pin not found."
        )

    # -----------------------------------------------------
    # EXAMPLE GPIO ACCESS
    # -----------------------------------------------------

    gpio1 = get_gpio_pin(mcu, 1)
    gpio2 = get_gpio_pin(mcu, 2)

    if gpio1:
        print("[INFO] GPIO1 resolved.")

    if gpio2:
        print("[INFO] GPIO2 resolved.")

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
        library='Device',
        symbol='R',
        value='4.7k',
        footprint='Resistor_SMD:R_0603_1608Metric'
    )

    r_scl = safe_part(
        library='Device',
        symbol='R',
        value='4.7k',
        footprint='Resistor_SMD:R_0603_1608Metric'
    )

    # -----------------------------------------------------
    # CONNECTIONS
    # -----------------------------------------------------

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
        library='Device',
        symbol='LED',
        footprint='LED_SMD:LED_0603_1608Metric'
    )

    res = safe_part(
        library='Device',
        symbol='R',
        value='330',
        footprint='Resistor_SMD:R_0603_1608Metric'
    )

    # -----------------------------------------------------
    # CONNECTIONS
    # -----------------------------------------------------

    res[1] += signal_net

    res[2] += led[2]

    led[1] += gnd_net

    return led, res

# =========================================================
# OPTIONAL ERC CHECK
# =========================================================

def run_basic_checks(parts):

    print("\n[INFO] Running basic checks...\n")

    for part in parts:

        try:

            print(
                f"Part: {part.name} | "
                f"Ref: {part.ref}"
            )

        except Exception:
            pass

    print("\n[INFO] Basic checks complete.\n")
