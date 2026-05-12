from skidl import Net, generate_netlist, KICAD, set_default_tool, Part
from libraries.pragyan_symbols import (
    PowerStage_LDO_3V3, 
    ESP32_Minimal_System, 
    I2C_Pullups,
    Status_LED
)

# Force SKiDL to use KiCad format for output compatibility
set_default_tool(KICAD)

class SchematicGenerator:
    def __init__(self, project_name="PragyanAI_Design"):
        """
        Initializes the Schematic Generator.
        
        Args:
            project_name: The base name for the generated .net file.
        """
        self.project_name = project_name
        # Define Global Rails
        self.gnd = Net('GND')
        self.v_in = Net('VCC_IN') # Typically 5V or 12V from DC Jack

    def build_from_plan(self, plan, mapped_data):
        """
        Translates the mapped data into a connected SKiDL circuit.
        
        Args:
            plan: The original requirement plan.
            mapped_data: The output from FootprintMapper with physical part info.
        """
        # 1. SYNTHESIZE POWER STAGE
        # We assume a 3.3V system requirement for modern AI IoT
        v33, ldo_reg = PowerStage_LDO_3V3(self.v_in, self.gnd)
        
        # 2. SYNTHESIZE MCU CORE
        # This macro adds the ESP32 plus reset/boot circuitry
        mcu = ESP32_Minimal_System(v33, self.gnd)
        
        # 3. SYNTHESIZE INTERFACES
        interfaces = mapped_data.get("interfaces", {})
        
        # Handle I2C Bus if requested
        if "I2C" in interfaces.values():
            sda = Net('SDA')
            scl = Net('SCL')
            
            # Connect to MCU (Standard ESP32-S3 pins: GPIO1=SDA, GPIO2=SCL)
            mcu['GPIO1'] += sda 
            mcu['GPIO2'] += scl
            
            # Apply Pull-up resistors automatically
            I2C_Pullups(sda, scl, v33)
            
        # 4. ADD PERIPHERALS
        # Add a Power-On Status LED
        Status_LED(v33, self.gnd, color="GREEN")

    def generate_netlist(self, output_path):
        """
        Compiles the SKiDL objects into a KiCad-readable netlist file.
        """
        try:
            generate_netlist(file_name=output_path)
            return True
        except Exception as e:
            print(f"Error during netlist generation: {e}")
            raise e

if __name__ == "__main__":
    # Internal validation logic
    gen = SchematicGenerator(project_name="Debug_Build")
    
    # Mock mapped data
    mock_mapped = {
        "interfaces": {"Display": "I2C"},
        "mcu": {"family": "ESP32-S3"}
    }
    
    gen.build_from_plan({}, mock_mapped)
    gen.generate_netlist("outputs/netlists/debug.net")
