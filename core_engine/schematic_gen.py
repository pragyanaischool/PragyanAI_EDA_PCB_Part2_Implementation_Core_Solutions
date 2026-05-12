import sys
import os
import logging
# lib_search_paths is the modern, robust way to manage library locations
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config, lib_search_paths

# --- 1. PATH STABILIZATION ---
# Ensures the root directory is accessible for module imports across the project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. KICAD CLOUD INFRASTRUCTURE CONFIG ---
# Points to the system KiCad symbols folder on the Streamlit Linux server
kicad_sym_path = '/usr/share/kicad/symbols/'

if os.path.exists(kicad_sym_path):
    # Add the path directly to SKiDL's internal search list for KiCad
    if kicad_sym_path not in lib_search_paths[KICAD]:
        lib_search_paths[KICAD].append(kicad_sym_path)
    logging.info(f"Hardware Library Path Indexed: {kicad_sym_path}")
else:
    logging.warning("Hardware Library directory not found. Ensure 'kicad' is in packages.txt")

# Standard PragyanAI Hardware Macros
from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3, 
    ESP32_Minimal_System, 
    I2C_Pullups,
    Status_LED
)

logger = logging.getLogger("PragyanAI-SchematicGen")

# Lock the engine to KiCad output format
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the generator with global nets (GND, VCC).
        """
        self.project_name = project_name
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def _safe_connect(self, part, net, aliases):
        """
        Heuristic Connection Logic:
        Prevents NoneType crashes by verifying pin availability before wiring.
        This is critical for cross-version KiCad library support.
        """
        for alias in aliases:
            try:
                # Check if the specific symbol actually contains this pin
                if part[alias] is not None:
                    part[alias] += net
                    logger.info(f"Matched {net.name} to {part.name} (Pin: {alias})")
                    return True
            except (KeyError, AttributeError, TypeError):
                continue
        
        logger.warning(f"Pin Mapping Alert: Net {net.name} skipped for {part.name}")
        return False

    def build_from_plan(self, plan, mapped_data):
        """
        Synthesizes the physical circuit layout using Heuristic Mapping.
        """
        try:
            logger.info(f"Synthesizing PragyanAI Implementation Core: {self.project_name}")
            
            # 1. CORE POWER & PROCESSING
            # Generates the 3.3V LDO stage and the MCU subsystem
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 2. PERIPHERAL INTERFACE SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            # Check if AI architecture requires I2C connectivity
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Dynamic Pin Mapping for ESP32-S3 (Standard pins 4 & 5)
                # We try logical names, IO prefixes, and physical indices
                self._safe_connect(mcu, sda, ['GPIO1', 'IO1', 'G1', 4, 'SDA'])
                self._safe_connect(mcu, scl, ['GPIO2', 'IO2', 'G2', 5, 'SCL'])
                
                # Apply bus pull-up resistors for electrical integrity
                I2C_Pullups(sda, scl, v33)
                
            # 3. GLOBAL STATUS HARDWARE
            # LED tied to the 3.3V rail to indicate power-on state
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis CRITICAL FAILURE: {str(e)}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the in-memory circuit to a physical KiCad .net file.
        """
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # SKiDL global generation call
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist artifact created: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Artifact generation failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test harness for synthesis validation
    gen = SchematicGenerator(project_name="Unit_Test_Build")
    test_mapped = {"interfaces": {"Sensor": "I2C"}}
    if gen.build_from_plan({}, test_mapped):
        gen.generate_netlist("outputs/netlists/test.net")
