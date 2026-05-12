import pandas as pd
import os
import logging
from datetime import datetime

# Initialize logging
logger = logging.getLogger("PragyanAI-BOM")

class BOMManager:
    def __init__(self, output_dir="outputs/boms/"):
        """
        Initializes the BOM Manager.
        
        Args:
            output_dir: Directory where the generated CSVs will be saved.
        """
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def export_bom(self, plan, filename=None):
        """
        Compiles the Bill of Materials from the enriched architecture plan.
        
        Args:
            plan (dict): The plan after being processed by FootprintMapper.
            filename (str): Optional custom filename.
        """
        if not plan or 'mcu' not in plan:
            logger.error("BOM Generation Failed: Invalid or empty plan.")
            raise KeyError("The plan must contain at least an 'mcu' definition.")

        project_name = plan.get("project_name", "PragyanAI_Project")
        if filename is None:
            filename = os.path.join(self.output_dir, f"{project_name}_BOM.csv")

        bom_data = []

        # 1. Process Microcontroller (Designator U1)
        mcu = plan.get("mcu", {})
        bom_data.append({
            "Designator": "U1",
            "Quantity": 1,
            "Value": mcu.get("family", "MCU"),
            "MPN": mcu.get("mpn", "UNKNOWN"),
            "Footprint": mcu.get("footprint", "GENERIC"),
            "Manufacturer": mcu.get("manufacturer", "GENERIC"),
            "Description": f"Main Controller: {mcu.get('family')}"
        })

        # 2. Process Power Components (Designators U2, U3...)
        for i, pwr in enumerate(plan.get("power_tree", []), start=2):
            bom_data.append({
                "Designator": f"U{i}",
                "Quantity": 1,
                "Value": f"{pwr.get('output_v')}V Regulator",
                "MPN": pwr.get("mpn", "UNKNOWN"),
                "Footprint": pwr.get("footprint", "GENERIC"),
                "Manufacturer": pwr.get("manufacturer", "GENERIC"),
                "Description": f"{pwr.get('component')} ({pwr.get('input_v')}V to {pwr.get('output_v')}V)"
            })

        # 3. Process Passives / Standard Support Parts
        # Logic: We add common passives required by our pragyan_symbols macros
        # In a full-scale system, these would be tracked via the SKiDL circuit object
        passives = [
            {"Designator": "C1, C2", "Qty": 2, "Val": "10uF", "MPN": "CL21A106KAYNNNE", "Foot": "0603", "Desc": "Decoupling Cap"},
            {"Designator": "R1, R2", "Qty": 2, "Val": "4.7k", "MPN": "RC0603FR-074K7L", "Foot": "0603", "Desc": "I2C Pull-ups"}
        ]
        
        for p in passives:
            bom_data.append({
                "Designator": p["Designator"],
                "Quantity": p["Qty"],
                "Value": p["Val"],
                "MPN": p["MPN"],
                "Footprint": f"Resistor_SMD:R_{p['Foot']}_1608Metric",
                "Manufacturer": "Samsung/Yageo",
                "Description": p["Desc"]
            })

        # 4. Generate CSV using Pandas
        df = pd.DataFrame(bom_data)
        
        try:
            df.to_csv(filename, index=False)
            logger.info(f"BOM successfully exported to {filename}")
            print(f"✅ BOM Generated: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to write BOM CSV: {e}")
            raise e

if __name__ == "__main__":
    # Test execution
    manager = BOMManager()
    sample_mapped_plan = {
        "project_name": "SmartGate_V1",
        "mcu": {
            "family": "ESP32-S3",
            "mpn": "ESP32-S3-WROOM-1-N8",
            "footprint": "RF_Module:ESP32-S3-WROOM-1-N8",
            "manufacturer": "Espressif"
        },
        "power_tree": [
            {"component": "LDO", "output_v": 3.3, "mpn": "AMS1117-3.3", "footprint": "SOT-223"}
        ]
    }
    manager.export_bom(sample_mapped_plan)
