import sys
import os
import logging
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config

# --- 1. PATH STABILIZATION ---
# Ensures root directory is accessible for importing from 'libraries'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. KICAD ENVIRONMENT CONFIG ---
# Directs SKiDL to the system KiCad symbols folder on Streamlit/Linux
kicad_sym_path = '/usr/share/kicad/symbols/'
if os.path.exists(kicad_sym_path):
    config.lib_search_paths[KICAD].append(kicad_sym_path)

from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3, 
    ESP32_Minimal_System, 
    I2C_Pullups,
    Status_LED
)

logger = logging.getLogger("PragyanAI-SchematicGen")

# Force SKiDL to output KiCad-compatible netlists
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the generator with standard global nets.
        """
        self.project_name = project_name
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def _safe_connect(self, part, net, aliases):
        """
        Helper: Attempts to connect a net to a part using a list of possible aliases.
        Prevents NoneType errors by checking pin availability before wiring.
        """
        for alias in aliases:
            try:
                # Check if the symbol actually contains this pin
                if part[alias] is not None:
                    part[alias] += net
                    logger.info(f"Successfully mapped {net.name} to pin: {alias}")
                    return True
            except (KeyError, AttributeError, TypeError):
                continue
        
        logger.warning(f"Pin Mapping Alert: Could not find any of {aliases} for net {net.name}")
        return False

    def build_from_plan(self, plan, mapped_data):
        """
        Synthesizes the physical circuit layout using heuristic mapping.
        """
        try:
            logger.info(f"Starting Implementation Core Synthesis: {self.project_name}")
            
            # 1. GENERATE CORE SUBSYSTEMS
            # Build the 3.3V power rail and the MCU system
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 2. PERIPHERAL BUS SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            # If the AI Architecture requires an I2C bus
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Heuristic Pin Mapping for I2C (ESP32-S3 common pins)
                # We try logical names, vendor labels, and physical pin indices
                self._safe_connect(mcu, sda, ['GPIO1', 'IO1', 'G1', 4, 'SDA'])
                self._safe_connect(mcu, scl, ['GPIO2', 'IO2', 'G2', 5, 'SCL'])
                
                # Add pull-up resistors to ensure bus stability
                I2C_Pullups(sda, scl, v33)
                
            # 3. GLOBAL STATUS HARDWARE
            # Active-high Power LED tied to the 3.3V rail
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis CRITICAL FAILURE: {str(e)}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the synthesized in-memory circuit to a physical .net file.
        """
        try:
            # Create output directory if it doesn't exist (prevents OS errors)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # SKiDL global generation call
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist artifact generated successfully at: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Artifact generation failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test harness for local validation
    test_mapped = {"interfaces": {"Sensor": "I2C"}}
    gen = SchematicGenerator(project_name="Unit_Test_Build")
    if gen.build_from_plan({}, test_mapped):
        gen.generate_netlist("outputs/netlists/test_output.net")
        
