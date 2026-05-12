import sys
import os
import logging
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part

# --- PATH INJECTION ---
# Ensures the root directory is accessible so 'libraries' can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3, 
    ESP32_Minimal_System, 
    I2C_Pullups,
    Status_LED
)

# Set global logger
logger = logging.getLogger("PragyanAI-SchematicGen")

# Force SKiDL to use KiCad format
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the Schematic Generator.
        """
        self.project_name = project_name
        # Define Global Nets (Common across all macros)
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def build_from_plan(self, plan, mapped_data):
        """
        Wires the circuit programmatically based on the mapped architecture.
        """
        try:
            logger.info(f"Starting circuit synthesis for project: {self.project_name}")
            
            # 1. GENERATE POWER RAIL
            # Macro provides a 3.3V rail from V_IN
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            
            # 2. GENERATE MCU CORE
            # Macro handles ESP32-S3 and its supporting components
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 3. INTERFACE SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            # If the architecture requires I2C (common for sensors/displays)
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Connect to standard S3 Pins
                mcu['GPIO1'] += sda 
                mcu['GPIO2'] += scl
                
                # Automatically apply the required pull-up resistors
                I2C_Pullups(sda, scl, v33)
                logger.info("I2C Bus synthesized with pull-up resistors.")
                
            # 4. SAFETY & INDICATORS
            # Add a power-on LED to indicate the 3.3V rail is active
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis failed during building: {e}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the in-memory SKiDL circuit to a physical .net file.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # SKiDL global generation call
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist successfully written to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate netlist file: {e}")
            raise e

if __name__ == "__main__":
    # Test block for local validation
    test_mapped = {
        "interfaces": {"Display": "I2C"},
        "mcu": {"family": "ESP32-S3"}
    }
    gen = SchematicGenerator(project_name="Build_Test")
    gen.build_from_plan({}, test_mapped)
    gen.generate_netlist("outputs/netlists/test.net")
    
