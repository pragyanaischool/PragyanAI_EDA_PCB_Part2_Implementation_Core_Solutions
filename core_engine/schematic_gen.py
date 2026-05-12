import sys
import os
import logging
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config

# --- 1. PATH INJECTION ---
# Ensures the root directory is accessible so the 'libraries' folder is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. KICAD LIBRARY PATH FINDER (For Streamlit/Linux) ---
# We must explicitly point SKiDL to the KiCad symbol directory on the server
kicad_sym_path = '/usr/share/kicad/symbols/'
if os.path.exists(kicad_sym_path):
    config.lib_search_paths[KICAD].append(kicad_sym_path)

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
        Initializes the Schematic Generator with global nets.
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
            
            # 1. POWER STAGE SYNTHESIS
            # Macro provides a 3.3V rail from V_IN including capacitors
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            
            # 2. MCU CORE SYNTHESIS
            # Macro handles ESP32-S3 and its supporting components (EN pull-up, etc.)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 3. INTERFACE SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            # Identify if I2C is required (e.g., for sensors or OLEDs)
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Connect to standard S3 Pins (GPIO1=SDA, GPIO2=SCL)
                mcu['GPIO1'] += sda 
                mcu['GPIO2'] += scl
                
                # Automatically apply the required 4.7k pull-up resistors
                I2C_Pullups(sda, scl, v33)
                logger.info("I2C Bus synthesized with pull-up resistors.")
                
            # 4. VISUAL INDICATORS
            # Add a power-on LED to indicate the 3.3V rail is healthy
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis failed during building: {e}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the in-memory SKiDL circuit to a physical .net file for KiCad.
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # SKiDL global generation call
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist successfully written to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to generate netlist file: {e}")
            raise e

if __name__ == "__main__":
    # Internal validation logic
    test_mapped = {
        "interfaces": {"Display": "I2C"},
        "mcu": {"family": "ESP32-S3"}
    }
    gen = SchematicGenerator(project_name="Debug_Build")
    gen.build_from_plan({}, test_mapped)
    gen.generate_netlist("outputs/netlists/debug.net")
    
    
