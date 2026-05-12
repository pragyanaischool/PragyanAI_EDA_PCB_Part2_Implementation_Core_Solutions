import sys
import os
import logging
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config

# --- 1. PATH INJECTION ---
# Ensures the engine can locate the 'libraries' folder in the Streamlit environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. CLOUD ENVIRONMENT CONFIG ---
# Points to the system KiCad symbols on the Streamlit Linux server
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

# Set default CAD tool to KiCad
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the generator with core power and ground nets.
        """
        self.project_name = project_name
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def _safe_connect(self, part, net, aliases):
        """
        Heuristic Connection Logic:
        Prevents NoneType errors by checking if a pin exists (by name or index)
        before attempting to wire it.
        """
        for alias in aliases:
            try:
                # SKiDL returns None if the pin doesn't exist; this check is critical
                if part[alias] is not None:
                    part[alias] += net
                    logger.info(f"Successfully mapped {net.name} to {part.name} pin: {alias}")
                    return True
            except (KeyError, AttributeError, TypeError):
                continue
        
        logger.warning(f"Heuristic Alert: Could not map {net.name} to any aliases in {part.name}")
        return False

    def build_from_plan(self, plan, mapped_data):
        """
        Executes the synthesis of the hardware architecture.
        """
        try:
            logger.info(f"Synthesizing PragyanAI Implementation Core: {self.project_name}")
            
            # 1. CORE POWER & PROCESSING
            # Generate 3.3V Rail and MCU Core
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 2. PERIPHERAL INTERFACES
            interfaces = mapped_data.get("interfaces", {})
            
            # If the design requires I2C (e.g., for sensors)
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Apply Heuristic Mapping: Try logical names, IO names, and Pin numbers
                # Standard ESP32-S3 pins: SDA is GPIO1 (Pin 4), SCL is GPIO2 (Pin 5)
                self._safe_connect(mcu, sda, ['GPIO1', 'IO1', 'G1', 4, 'SDA'])
                self._safe_connect(mcu, scl, ['GPIO2', 'IO2', 'G2', 5, 'SCL'])
                
                # Connect pull-up resistors for the I2C bus
                I2C_Pullups(sda, scl, v33)
                
            # 3. VISUAL STATUS INDICATORS
            # Add a power-on LED (Active High)
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis Failure: {str(e)}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the in-memory circuit to a physical .net file.
        """
        try:
            # Create output directory path if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate the KiCad netlist
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist artifact generated at: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Netlist generation failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Internal Unit Test
    test_gen = SchematicGenerator(project_name="Cloud_Validation_Build")
    mock_mapped = {"interfaces": {"Sensor": "I2C"}}
    if test_gen.build_from_plan({}, mock_mapped):
        test_gen.generate_netlist("outputs/netlists/cloud_test.net")
