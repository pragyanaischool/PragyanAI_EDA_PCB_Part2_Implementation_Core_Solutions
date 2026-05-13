import logging

# Configure local logger
logger = logging.getLogger("PragyanAI-Mapper")

class FootprintMapper:
    def __init__(self):
        """
        The FootprintMapper bridges the gap between the Planning Engine (Logic)
        and the Implementation Core (Physical).
        """
        # --- PHYSICAL FOOTPRINT LIBRARY MAP ---
        # These strings correspond to standard KiCad library footprints.
        self.library_map = {
            "mcu": "RF_Module:ESP32-S3-WROOM-1-N8",
            "ldo": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
            "resistor": "Resistor_SMD:R_0603_1608Metric",
            "capacitor": "Capacitor_SMD:C_0603_1608Metric",
            "led": "LED_SMD:LED_0603_1608Metric",
            "i2c_sensor": "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
            "spi_sensor": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
            "generic": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
        }

    def map(self, plan_data):
        """
        Main entry point called by ImplementationWorker.
        Translates the Architecture JSON into a list of physical component definitions.
        """
        logger.info("Starting footprint mapping logic...")
        mapped_components = []

        try:
            # 1. Map the Core MCU
            mcu_info = plan_data.get("mcu", {})
            mcu_family = mcu_info.get("family", "ESP32-S3")
            
            mapped_components.append({
                "id": "U1",
                "type": "mcu",
                "label": mcu_family,
                "footprint": self.library_map["mcu"],
                "value": mcu_family
            })

            # 2. Map the Power Stage (LDO)
            # Every PragyanAI design currently assumes a standard LDO for 3.3V
            mapped_components.append({
                "id": "U2",
                "type": "ldo",
                "label": "AMS1117-3.3",
                "footprint": self.library_map["ldo"],
                "value": "AMS1117-3.3"
            })

            # 3. Map Peripherals/Sensors from the JSON 'components' list
            # We iterate through user-defined sensors and assign pin headers/footprints
            for i, comp in enumerate(plan_data.get("components", []), start=1):
                comp_name = comp.get("name", f"Peripheral_{i}")
                comp_type = comp.get("type", "generic").lower()
                
                # Determine footprint based on protocol or type
                # Heuristic: If it has I2C in the name, give it a 4-pin header
                if "i2c" in comp_name.lower():
                    fp = self.library_map["i2c_sensor"]
                elif "spi" in comp_name.lower():
                    fp = self.library_map["spi_sensor"]
                else:
                    fp = self.library_map.get(comp_type, self.library_map["generic"])

                mapped_components.append({
                    "id": f"J{i}",  # J stands for Jack/Header for external modules
                    "type": comp_type,
                    "label": comp_name,
                    "footprint": fp,
                    "value": comp_name
                })

            logger.info(f"Mapping Success: {len(mapped_components)} components localized.")
            return mapped_components

        except Exception as e:
            logger.error(f"Mapping Failed: {str(e)}")
            # Return at least the MCU and LDO so the synthesis doesn't crash completely
            return mapped_components
