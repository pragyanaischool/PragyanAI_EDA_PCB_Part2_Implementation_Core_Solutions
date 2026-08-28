import os
import numpy as np
import pandas as pd

def generate_pcb_dataset(num_samples: int = 1200, output_path: str = "data/pcb_manufacturing_data.csv"):
    np.random.seed(42)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    board_ids = [f"PCB_{1000 + i}" for i in range(num_samples)]
    layers = np.random.choice([2, 4, 6, 8], size=num_samples, p=[0.2, 0.4, 0.3, 0.1])
    component_count = np.random.randint(40, 250, size=num_samples)
    
    # Process & Physical Measurements
    solder_thickness_um = np.random.normal(loc=125, scale=18, size=num_samples) # Nominally 120-130 um
    reflow_temp_c = np.random.normal(loc=245, scale=12, size=num_samples)        # Nominally 240-250 C
    conveyor_speed_cm_min = np.random.normal(loc=65, scale=8, size=num_samples)
    pad_clearance_mm = np.random.uniform(0.12, 0.35, size=num_samples)
    inspection_vibration_g = np.random.exponential(scale=0.08, size=num_samples)
    ambient_humidity_pct = np.random.uniform(35.0, 65.0, size=num_samples)
    
    # Simulate Defect Logic
    defect_types = []
    status = []
    
    for i in range(num_samples):
        # Stress conditions leading to defects
        temp = reflow_temp_c[i]
        thick = solder_thickness_um[i]
        vib = inspection_vibration_g[i]
        
        if temp > 265 or (temp > 255 and thick < 95):
            defect_types.append("Tombstoning")
            status.append("Fail")
        elif thick > 160 or (thick > 145 and pad_clearance_mm[i] < 0.15):
            defect_types.append("Short Circuit")
            status.append("Fail")
        elif thick < 90 or temp < 225:
            defect_types.append("Open Solder")
            status.append("Fail")
        elif vib > 0.30:
            defect_types.append("Missing Component")
            status.append("Fail")
        elif np.random.rand() < 0.04:
            defect_types.append("Spur")
            status.append("Fail")
        else:
            defect_types.append("None")
            status.append("Pass")
            
    df = pd.DataFrame({
        "board_id": board_ids,
        "layer_count": layers,
        "component_count": component_count,
        "solder_thickness_um": np.round(solder_thickness_um, 2),
        "reflow_temp_c": np.round(reflow_temp_c, 2),
        "conveyor_speed_cm_min": np.round(conveyor_speed_cm_min, 2),
        "pad_clearance_mm": np.round(pad_clearance_mm, 3),
        "vibration_g": np.round(inspection_vibration_g, 4),
        "ambient_humidity_pct": np.round(ambient_humidity_pct, 2),
        "defect_type": defect_types,
        "quality_status": status
    })
    
    df.to_csv(output_path, index=False)
    print(f" Dataset successfully saved to '{output_path}' ({num_samples} records).")
    print(f" Class Distribution:\n{df['quality_status'].value_counts(normalize=True)}")

if __name__ == "__main__":
    generate_pcb_dataset()
