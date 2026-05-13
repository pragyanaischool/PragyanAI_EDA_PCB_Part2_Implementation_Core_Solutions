import os
import json
import logging
from rich.console import Console
from core_engine.schematic_gen import SchematicGenerator
from core_engine.bom_manager import BOMManager
from core_engine.footprint_mapper import FootprintMapper

import sys

# Forces the project root into the Python Path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Initialize logging and console for PragyanAI Studio
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PragyanAI-Implementation")

class ImplementationWorker:
    def __init__(self, plan_path: str, output_dir: str = "outputs/netlists/"):
        """
        Initializes the Implementation Worker.
        
        Args:
            plan_path: Path to the architecture_plan.json from Element 1.
            output_dir: Where the generated KiCad netlist will be stored.
        """
        self.plan_path = plan_path
        self.output_dir = output_dir
        self.mapper = FootprintMapper()
        self.bom_manager = BOMManager()
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_architecture_plan(self):
        """Loads and validates the JSON plan."""
        try:
            with open(self.plan_path, 'r') as f:
                plan = json.load(f)
            console.print("[bold green]SUCCESS:[/bold green] Architecture Plan Loaded.")
            return plan
        except Exception as e:
            console.print(f"[bold red]ERROR:[/bold red] Failed to load plan: {e}")
            return None

    def run(self):
        """Executes the full hardware implementation sequence."""
        console.print("[bold cyan]PragyanAI Worker:[/bold cyan] Starting Implementation Core...")

        # 1. Load Data
        plan = self.load_architecture_plan()
        if not plan:
            return

        # 2. Map Components to Physical Inventory
        # This step translates "ESP32-S3" -> "RF_Module:ESP32-S3-WROOM-1"
        console.print("Mapping logical components to footprints...")
        mapped_components = self.mapper.assign_footprints(plan)

        # 3. Generate Circuit (SKiDL)
        # This creates the electrical connections (nets)
        console.print("Synthesizing electrical netlist via SKiDL...")
        generator = SchematicGenerator(project_name=plan.get("project_name", "PragyanAI_Design"))
        
        try:
            generator.build_from_plan(plan, mapped_components)
            
            # 4. Final Export
            output_file = os.path.join(self.output_dir, f"{generator.project_name}.net")
            generator.generate_netlist(output_path=output_file)
            
            # 5. BOM Generation
            console.print("Generating Bill of Materials (BOM)...")
            self.bom_manager.export_bom(plan, filename=f"outputs/boms/{generator.project_name}_BOM.csv")
            
            console.print(f"[bold green]🏁 PROCESS COMPLETE:[/bold green] Netlist saved to {output_file}")
            
        except Exception as e:
            console.print(f"[bold red]CRITICAL FAILURE:[/bold red] Schematic synthesis failed: {str(e)}")

if __name__ == "__main__":
    # In production, this would be triggered by a file upload or a webhook from Element 1
    worker = ImplementationWorker(plan_path="architecture_plan.json")
    worker.run()
  
