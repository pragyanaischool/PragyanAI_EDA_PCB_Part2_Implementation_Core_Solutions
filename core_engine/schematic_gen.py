import sys
import os
import logging
# lib_search_paths is the modern way to manage library locations
from skidl import Net, generate_netlist, KICAD, set_default_tool, Part, config, lib_search_paths

# --- 1. PATH STABILIZATION ---
# Ensures the root directory is accessible for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 2. KICAD CLOUD INFRASTRUCTURE CONFIG ---
# Target the standard Linux KiCad symbols folder
kicad_sym_path = '/usr/share/kicad/symbols/'

if os.path.exists(kicad_sym_path):
    # Add path directly to the SKiDL library search paths
    if kicad_sym_path not in lib_search_paths[KICAD]:
        lib_search_paths[KICAD].append(kicad_sym_path)
    logging.info(f"KiCad symbol path indexed: {kicad_sym_path}")
else:
    logging.warning("KiCad symbols folder not found. Check packages.txt for 'kicad'.")

# Standard PragyanAI Symbol Macros
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
        Initializes the generator with global power and ground nets.
        """
        self.project_name = project_name
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') 

    def _safe_connect(self, part, net, aliases):
        """
        Heuristic Connection Logic:
        Safeguards against NoneType errors by verifying pin existence 
        before wiring, supporting cross-library compatibility.
        """
        for alias in aliases:
            try:
                # SKiDL returns None if the pin name/number isn't in the symbol
                if part[alias] is not None:
                    part[alias] += net
                    logger.info(f"Mapped {net.name} -> {part.name} (Pin: {alias})")
                    return True
            except (KeyError, AttributeError, TypeError):
                continue
        
        logger.warning(f"Pin Mapping Alert: {net.name} skipped for {part.name}")
        return False

    def build_from_plan(self, plan, mapped_data):
        """
        Executes the synthesis of the hardware architecture.
        """
        try:
            logger.info(f"Starting Implementation Core Synthesis: {self.project_name}")
            
            # 1. CORE POWER & PROCESSING
            v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
            mcu = ESP32_Minimal_System(v33, self.gnd)
            
            # 2. PERIPHERAL INTERFACE SYNTHESIS
            interfaces = mapped_data.get("interfaces", {})
            
            if "I2C" in interfaces.values():
                sda = Net('SDA')
                scl = Net('SCL')
                
                # Dynamic Pin Mapping for ESP32-S3 (Standard pins 4 & 5)
                self._safe_connect(mcu, sda, ['GPIO1', 'IO1', 'G1', 4, 'SDA'])
                self._safe_connect(mcu, scl, ['GPIO2', 'IO2', 'G2', 5, 'SCL'])
                
                # Apply pull-up resistors to the bus
                I2C_Pullups(sda, scl, v33)
                
            # 3. GLOBAL STATUS INDICATORS
            Status_LED(v33, self.gnd, color="GREEN")
            
            return True

        except Exception as e:
            logger.error(f"Synthesis CRITICAL FAILURE: {str(e)}")
            raise e

    def generate_netlist(self, output_path):
        """
        Exports the synthesized circuit to a physical .net file.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            generate_netlist(file_name=output_path)
            logger.info(f"Netlist artifact created: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Artifact generation failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test harness
    gen = SchematicGenerator(project_name="Unit_Test_Build")
    test_data = {"interfaces": {"Sensor": "I2C"}}
    if gen.build_from_plan({}, test_data):
        gen.generate_netlist("outputs/netlists/test.net")
