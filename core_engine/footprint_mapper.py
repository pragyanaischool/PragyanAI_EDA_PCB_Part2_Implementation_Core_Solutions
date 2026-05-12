import json
import os
import logging

# Configure logging for the Mapper
logger = logging.getLogger("PragyanAI-Mapper")

class FootprintMapper:
    def __init__(self, db_path="libraries/mapping_db.json"):
        """
        Initializes the mapper and loads the component database.
        
        Args:
            db_path: Path to the JSON file containing MPN and footprint mappings.
        """
        self.db_path = db_path
        self.mapping_db = self._load_db()

    def _load_db(self):
        """Internal helper to load the mapping database from disk."""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}. Using empty fallback.")
            return {}
        try:
            with open(self.db_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing mapping_db.json: {e}")
            return {}

    def assign_footprints(self, plan):
        """
        Translates a logical architecture plan into physical engineering data.
        
        Args:
            plan (dict): The architecture plan from the Planning Engine.
            
        Returns:
            dict: The plan enriched with KiCad footprints, MPNs, and Manufacturers.
        """
        # 1. Initialize the mapped result
        mapped_data = {
            "project_name": plan.get("project_name", "Untitled_Pragyan_Project"),
            "mcu": {},
            "power_tree": [],
            "interfaces": plan.get("interfaces", {})
        }

        # 2. Map the Microcontroller (MCU)
        mcu_req = plan.get("mcu", {})
        mcu_family = mcu_req.get("family", "ESP32-S3")
        
        # Look up in database
        mcu_info = self.mapping_db.get("mcu", {}).get(mcu_family)
        
        if mcu_info:
            mapped_data["mcu"] = {
                "family": mcu_family,
                "part": mcu_info.get("part"),
                "library": mcu_info.get("library"),
                "footprint": mcu_info.get("footprint"),
                "mpn": mcu_info.get("mpn"),
                "manufacturer": mcu_info.get("manufacturer")
            }
        else:
            # Fallback for unknown parts to prevent system crash
            logger.warning(f"Part {mcu_family} not in database. Using Generic fallback.")
            mapped_data["mcu"] = {
                "family": mcu_family,
                "footprint": "RF_Module:Generic_Module",
                "mpn": "UNKNOWN",
                "manufacturer": "GENERIC"
            }

        # 3. Map Power Components
        for item in plan.get("power_tree", []):
            # Basic logic: select regulator based on requested output voltage
            target_v = item.get("output_v")
            comp_key = "AMS1117-3.3" if target_v == 3.3 else "LM2596-5.0"
            
            pwr_info = self.mapping_db.get("regulators", {}).get(comp_key, {})
            
            # Combine the PRD requirement with the physical part data
            mapped_data["power_tree"].append({
                "component": item.get("component"),
                "input_v": item.get("input_v"),
                "output_v": target_v,
                "part": pwr_info.get("part"),
                "footprint": pwr_info.get("footprint"),
                "mpn": pwr_info.get("mpn"),
                "manufacturer": pwr_info.get("manufacturer")
            })

        return mapped_data

if __name__ == "__main__":
    # Quick Test Loop
    test_plan = {
        "mcu": {"family": "ESP32-S3"},
        "power_tree": [{"component": "LDO", "output_v": 3.3}]
    }
    mapper = FootprintMapper()
    print(json.dumps(mapper.assign_footprints(test_plan), indent=2))
