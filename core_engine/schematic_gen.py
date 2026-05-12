import sys
import os
import logging
import skidl

from skidl import (
    Net,
    generate_netlist,
    KICAD,
    set_default_tool,
    lib_search_paths,
    ERC
)

# =========================================================
# SKIDL CONFIGURATION
# =========================================================

if hasattr(skidl, 'config'):

    skidl.config.query_thread_safe = True
    skidl.config.cache_and_index = False

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

logger = logging.getLogger(
    "PragyanAI-SchematicGen"
)

# =========================================================
# KICAD LIBRARY CONFIGURATION
# =========================================================

kicad_sym_path = "/usr/share/kicad/symbols"

if os.path.exists(kicad_sym_path):

    if kicad_sym_path not in lib_search_paths[KICAD]:

        lib_search_paths[KICAD].append(
            kicad_sym_path
        )

    logger.info(
        f"Hardware Library Indexed: "
        f"{kicad_sym_path}"
    )

    print(
        f"[SKIDL] KiCad library indexed: "
        f"{kicad_sym_path}"
    )

else:

    logger.warning(
        "KiCad symbols folder not found."
    )

# =========================================================
# LOCK TO KICAD TOOLCHAIN
# =========================================================

set_default_tool(KICAD)

# =========================================================
# PRAGYANAI HARDWARE MACROS
# =========================================================

from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3,
    ESP32_Minimal_System,
    I2C_Pullups,
    Status_LED,
    get_gpio_pin
)

# =========================================================
# SCHEMATIC GENERATOR
# =========================================================

class SchematicGenerator:

    def __init__(
        self,
        project_name="PragyanAI_Design"
    ):

        self.project_name = project_name

        # -------------------------------------------------
        # GLOBAL NETS
        # -------------------------------------------------

        self.gnd = Net("GND")

        self.v_in = Net("VCC_IN")

        logger.info(
            f"Schematic Generator initialized: "
            f"{self.project_name}"
        )

    # =====================================================
    # SAFE CONNECTION
    # =====================================================

    def _safe_connect(
        self,
        pin,
        net,
        label=""
    ):

        try:

            if pin is None:

                logger.warning(
                    f"Pin missing for "
                    f"{label}"
                )

                return False

            pin += net

            logger.info(
                f"Connected "
                f"{net.name} -> {label}"
            )

            return True

        except Exception as e:

            logger.warning(
                f"Connection failed: "
                f"{label} -> {e}"
            )

            return False

    # =====================================================
    # MAIN SYNTHESIS ENGINE
    # =====================================================

    def build_from_plan(
        self,
        plan,
        mapped_data
    ):

        try:

            logger.info(
                f"Synthesizing: "
                f"{self.project_name}"
            )

            print(
                "\n[INFO] Starting "
                "schematic synthesis...\n"
            )

            # -------------------------------------------------
            # POWER STAGE
            # -------------------------------------------------

            print(
                "[INFO] Building power stage..."
            )

            v33, ldo_reg = PowerStage_LDO_3V3(
                self.v_in,
                self.gnd
            )

            print(
                "[INFO] Power stage complete."
            )

            # -------------------------------------------------
            # MCU STAGE
            # -------------------------------------------------

            print(
                "[INFO] Building ESP32 subsystem..."
            )

            mcu = ESP32_Minimal_System(
                v33,
                self.gnd
            )

            print(
                "[INFO] ESP32 subsystem complete."
            )

            # -------------------------------------------------
            # INTERFACES
            # -------------------------------------------------

            interfaces = mapped_data.get(
                "interfaces",
                {}
            )

            # -------------------------------------------------
            # I2C BUS
            # -------------------------------------------------

            if "I2C" in interfaces.values():

                print(
                    "[INFO] Configuring I2C bus..."
                )

                sda = Net("SDA")

                scl = Net("SCL")

                # ---------------------------------------------
                # SAFE GPIO RESOLUTION
                # ---------------------------------------------

                gpio_sda = get_gpio_pin(
                    mcu,
                    1
                )

                gpio_scl = get_gpio_pin(
                    mcu,
                    2
                )

                # ---------------------------------------------
                # CONNECT SDA
                # ---------------------------------------------

                self._safe_connect(
                    gpio_sda,
                    sda,
                    "ESP32 SDA"
                )

                # ---------------------------------------------
                # CONNECT SCL
                # ---------------------------------------------

                self._safe_connect(
                    gpio_scl,
                    scl,
                    "ESP32 SCL"
                )

                # ---------------------------------------------
                # I2C PULLUPS
                # ---------------------------------------------

                I2C_Pullups(
                    sda,
                    scl,
                    v33
                )

                print(
                    "[INFO] I2C bus configured."
                )

            # -------------------------------------------------
            # STATUS LED
            # -------------------------------------------------

            print(
                "[INFO] Adding power LED..."
            )

            Status_LED(
                v33,
                self.gnd,
                color="GREEN"
            )

            print(
                "[INFO] Status LED added."
            )

            # -------------------------------------------------
            # ERC CHECK
            # -------------------------------------------------

            print(
                "[INFO] Running ERC..."
            )

            try:

                ERC()

                print(
                    "[INFO] ERC complete."
                )

            except Exception as erc_error:

                logger.warning(
                    f"ERC warning: {erc_error}"
                )

            print(
                "\n[SUCCESS] "
                "Schematic synthesis complete.\n"
            )

            return True

        except Exception as e:

            logger.error(
                f"Synthesis CRITICAL FAILURE: "
                f"{str(e)}"
            )

            print(
                f"\n[CRITICAL FAILURE] "
                f"{str(e)}\n"
            )

            raise e

    # =====================================================
    # NETLIST EXPORT
    # =====================================================

    def generate_netlist(
        self,
        output_path
    ):

        try:

            output_dir = os.path.dirname(
                output_path
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            print(
                "[INFO] Generating netlist..."
            )

            generate_netlist(
                file_name=output_path
            )

            logger.info(
                f"Netlist generated: "
                f"{output_path}"
            )

            print(
                f"[SUCCESS] Netlist saved: "
                f"{output_path}"
            )

            return True

        except Exception as e:

            logger.error(
                f"Netlist generation failed: "
                f"{str(e)}"
            )

            print(
                f"\n[NETLIST FAILURE] "
                f"{str(e)}\n"
            )

            raise e

# =========================================================
# TEST HARNESS
# =========================================================

if __name__ == "__main__":

    print(
        "\n===================================="
    )

    print(
        " PragyanAI Schematic Engine Test"
    )

    print(
        "====================================\n"
    )

    gen = SchematicGenerator(
        project_name="Unit_Test_Build"
    )

    test_mapped = {
        "interfaces": {
            "Sensor": "I2C"
        }
    }

    success = gen.build_from_plan(
        {},
        test_mapped
    )

    if success:

        gen.generate_netlist(
            "outputs/netlists/test.net"
        )

        print(
            "\n===================================="
        )

        print(
            " BUILD SUCCESSFUL "
        )

        print(
            "====================================\n"
        )
