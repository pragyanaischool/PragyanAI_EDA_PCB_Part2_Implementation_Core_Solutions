import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from generate_sample_data import generate_pcb_dataset

def run_end_to_end_demo():
    print("=" * 60)
    print("  PragyanAI EDA PCB - End-to-End Execution Pipeline")
    print("=" * 60)
    
    # 1. Generate / Load Data
    data_path = "data/pcb_manufacturing_data.csv"
    generate_pcb_dataset(num_samples=1500, output_path=data_path)
    df = pd.read_csv(data_path)
    
    # 2. Automated EDA Phase
    print("\n--- [Phase 1: Exploratory Data Analysis (EDA)] ---")
    print(f"Dataset Shape: {df.shape}")
    print(f"Missing Values:\n{df.isnull().sum().to_dict()}")
    print("\nDefect Breakdown by Type:")
    print(df["defect_type"].value_counts())
    
    print("\nStatistical Overview of Process Parameters:")
    print(df[["solder_thickness_um", "reflow_temp_c", "vibration_g"]].describe())
    
    # 3. Preprocessing & Feature Selection
    print("\n--- [Phase 2: Feature Engineering & Preprocessing] ---")
    feature_cols = [
        "layer_count", "component_count", "solder_thickness_um",
        "reflow_temp_c", "conveyor_speed_cm_min", "pad_clearance_mm",
        "vibration_g", "ambient_humidity_pct"
    ]
    
    X = df[feature_cols]
    y = (df["quality_status"] == "Fail").astype(int)  # 1 for Fail (Defect), 0 for Pass
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. Model Training & Validation
    print("\n--- [Phase 3: Model Training (Random Forest)] ---")
    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"Validation Accuracy: {acc * 100:.2f}%\n")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Pass (No Defect)", "Fail (Defective)"]))
    
    # Feature Importances
    feat_importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("\nTop Predictors of PCB Defects:")
    print(feat_importance.to_string())
    
    # 5. Live Inference Demonstration
    print("\n--- [Phase 4: Live Inference Demonstration] ---")
    sample_pcb = pd.DataFrame([{
        "layer_count": 4,
        "component_count": 120,
        "solder_thickness_um": 172.5,  # High solder -> likely short
        "reflow_temp_c": 248.0,
        "conveyor_speed_cm_min": 64.0,
        "pad_clearance_mm": 0.14,
        "vibration_g": 0.05,
        "ambient_humidity_pct": 45.0
    }])
    
    sample_scaled = scaler.transform(sample_pcb[feature_cols])
    prediction = model.predict(sample_scaled)[0]
    prob = model.predict_proba(sample_scaled)[0][1]
    
    print(f"Sample Input Parameters:\n{sample_pcb.to_dict(orient='records')[0]}")
    print(f"Prediction: {'DEFECT DETECTED (FAIL)' if prediction == 1 else 'PASSED (NO DEFECT)'}")
    print(f"Failure Probability: {prob * 100:.1f}%")
    print("\n End-to-end execution completed successfully!")

if __name__ == "__main__":
    run_end_to_end_demo()
