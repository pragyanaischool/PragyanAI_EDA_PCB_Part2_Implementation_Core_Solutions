import sys
import os
import logging
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config, load_peripheral_libraries

# --- 1. PATH STABILIZATION ---
# Ensures the root directory is accessible for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. KICAD CLOUD INFRASTRUCTURE CONFIG ---
# Points to the system KiCad symbols on the Streamlit Linux server
kicad_sym_path = '/usr/share/kicad/symbols/'

if os.path.exists(kicad_sym_path):
    # Add path to the search list
    config.lib_search_paths[KICAD].append(kicad_sym_path)
    try:
        # CRITICAL FIX: Explicitly load/index the libraries into memory
        # This resolves: "Can't make a part without a library & part name"
        load_peripheral_libraries()
        logging.info("Hardware Libraries (Connector, Device, MCU) indexed successfully.")
    except Exception as e:
        logging.warning(f"Library indexing issue: {e}")

from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3, 
    ESP32_Minimal_System, 
    I2C_Pullups,
    Status_LED
)

logger = logging.getLogger("PragyanAI-SchematicGen")
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the generator with global nets.
        """
        self.project_name = project_name
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def _safe_connect(self, part, net, aliases):
        """
        Heuristic Connection Helper:
        Checks for pin existence before wiring to prevent NoneType crashes.
        """
        for alias in aliases:
            try:
                if part[alias] is not None:
                    part[alias] += net
                    logger.info(f"Mapped {net.name} -> {part.name} pin {alias}")
                    return True
            except (KeyError, AttributeError, TypeError):
                continue
        logger.warning(f"Pin Mapping Alert: {net.name} could not be connected to {part.name}")
        return False

    def build_from_plan(self, plan, mapped_data):
        """
        Synthesizes the electrical architecture using Heuristic Pin Mapping.
        """
        try:
            logger.info(f"Starting Implementation Core Synthesis: {self.project_name}")
            
            # 1. CORE POWER & PROCESSING
            # Generates the 3.3V rail and the ESP32-S3 subsystem
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 2. PERIPHERAL INTERFACE SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Dynamic Pin Mapping for ESP32-S3 (Pins 4 & 5 are standard for SDA/SCL)
                self._safe_connect(mcu, sda, ['GPIO1', 'IO1', 'G1', 4, 'SDA'])
                self._safe_connect(mcu, scl, ['GPIO2', 'IO2', 'G2', 5, 'SCL'])
                
                # Add bus pull-ups for electrical stability
                I2C_Pullups(sda, scl, v33)
                
            # 3. STATUS INDICATORS
            # Visual feedback for power-on state
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis CRITICAL FAILURE: {str(e)}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the in-memory circuit to a physical .net file.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            generate_netlist(file_name=output_path)
            logger.info(f"Synthesis Artifact Created: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Artifact generation failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Internal Unit Test
    gen = SchematicGenerator(project_name="Cloud_Live_Build")
    test_data = {"interfaces": {"Bus": "I2C"}}
    if gen.build_from_plan({}, test_data):
        gen.generate_netlist("outputs/netlists/synthesis_complete.net")
