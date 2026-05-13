import os
import json
import logging
from rich.console import Console

# Import the Implementation Core Engines
from core_engine.schematic_gen import SchematicGenerator
from core_engine.bom_manager import BOMManager
from core_engine.footprint_mapper import FootprintMapper

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("PragyanAI-Worker")
console = Console()

class ImplementationWorker:
    def __init__(self, plan_path="architecture_plan.json"):
        """
        The ImplementationWorker acts as the orchestrator for Element 2.
        It translates logical JSON plans into physical engineering artifacts.
        """
        self.plan_path = plan_path
        self.outputs_base = "outputs"
        self.plan_data = None
        
        # Ensure output directory structure exists
        for folder in ["netlists", "boms", "reports"]:
            os.makedirs(os.path.join(self.outputs_base, folder), exist_ok=True)

    def load_plan(self):
        """Loads the architecture plan from the local buffer."""
        try:
            if not os.path.exists(self.plan_path):
                logger.error(f"Architecture plan not found at {self.plan_path}")
                return False
            
            with open(self.plan_path, 'r') as f:
                self.plan_data = json.load(f)
            logger.info("SUCCESS: Architecture Plan Loaded.")
            return True
        except Exception as e:
            logger.error(f"Failed to load architecture plan: {e}")
            return False

    def run(self):
        """
        Executes the full Hardware Synthesis Pipeline.
        1. Mapping -> 2. Schematic/Netlist Synthesis -> 3. BOM Generation
        """
        console.print("[bold blue]PragyanAI Worker:[/bold blue] Starting Implementation Core...")

        # 1. Load the data from the Phase 1 buffer
        if not self.load_plan():
            return False

        proj_name = self.plan_data.get("project_name", "PragyanAI_Design").replace(" ", "_")

        try:
            # --- PHASE 1: FOOTPRINT MAPPING ---
            # Translates logical components to physical packages (U1, J1, etc.)
            logger.info("Mapping logical components to footprints...")
            mapper = FootprintMapper()
            # Returns a LIST of components for the schematic engine
            mapped_data = mapper.map(self.plan_data)

            # --- PHASE 2: SCHEMATIC SYNTHESIS (SKiDL) ---
            # Builds electrical connections and exports KiCad netlist
            logger.info("Synthesizing electrical netlist via SKiDL...")
            schematic_path = os.path.join(self.outputs_base, "netlists", f"{proj_name}.net")
            
            gen = SchematicGenerator(project_name=proj_name)
            # Pass BOTH the plan (dict) and mapped_data (list) to avoid TypeErrors
            if gen.build_from_plan(self.plan_data, mapped_data):
                gen.generate_netlist(schematic_path)

            # --- PHASE 3: PROCUREMENT BOM GENERATION ---
            # FIX: We pass self.plan_data (the Dict) instead of mapped_data (the List)
            # This allows BOMManager to use .get('mcu') and .get('power_tree')
            logger.info("Generating Procurement Bill of Materials (BOM)...")
            bom_path = os.path.join(self.outputs_base, "boms", f"{proj_name}_BOM.csv")
            
            bom_mgr = BOMManager()
            # Pass the full dictionary to satisfy the BOMManager requirements
            bom_mgr.generate(self.plan_data, bom_path)

            console.print(f"[bold green]SUCCESS:[/bold green] Engineering artifacts for '{proj_name}' are ready.")
            return True

        except Exception as e:
            logger.critical(f"Implementation failure: {str(e)}")
            # Raise the exception so the Streamlit UI can display the error to the user
            raise e

# Self-test block for local debugging
if __name__ == "__main__":
    worker = ImplementationWorker()
    worker.run()
    
    
