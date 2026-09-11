"""
AI Models Training Script
Diabetes + Heart Disease XGBoost Models
"""
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle
import os

print("=" * 60)
print("🤖 AI MODELS TRAINING")
print("=" * 60)

# ============================================================
# 1. DIABETES MODEL
# ============================================================
print("\n📊 [1/2] Training Diabetes Model...")

try:
    df_diab = pd.read_csv("diabetes.csv")
    print(f"   ✅ Data loaded: {df_diab.shape[0]} rows")
    
    X = df_diab.drop("Outcome", axis=1)
    y = df_diab["Outcome"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("   🤖 Training XGBoost...")
    diab_model = XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        random_state=42, eval_metric='logloss'
    )
    diab_model.fit(X_train, y_train)
    
    accuracy = accuracy_score(y_test, diab_model.predict(X_test))
    print(f"   ✅ Accuracy: {accuracy * 100:.2f}%")
    
    with open("diabetes_model.pkl", "wb") as f:
        pickle.dump(diab_model, f)
    print(f"   💾 Saved: diabetes_model.pkl")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================
# 2. HEART DISEASE MODEL
# ============================================================
print("\n❤️ [2/2] Training Heart Disease Model...")

try:
    heart_file = None
    for fname in ["heart.csv", "heart_disease_uci.csv"]:
        if os.path.exists(fname):
            heart_file = fname
            break
    
    df_heart = pd.read_csv(heart_file)
    print(f"   ✅ Data loaded from: {heart_file}")
    print(f"   📊 Shape: {df_heart.shape[0]} rows, {df_heart.shape[1]} cols")
    
    # Target column
    target_col = None
    for col in ["target", "num", "heart_disease", "output"]:
        if col in df_heart.columns:
            target_col = col
            break
    if not target_col:
        target_col = df_heart.columns[-1]
    
    print(f"   🎯 Target: {target_col}")
    
    # Numeric only
    df_heart = df_heart.select_dtypes(include=[np.number])
    
    # Binary target
    if df_heart[target_col].nunique() > 2:
        df_heart[target_col] = (df_heart[target_col] > 0).astype(int)
    
    X = df_heart.drop(target_col, axis=1)
    y = df_heart[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("   🤖 Training XGBoost...")
    heart_model = XGBClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.1,
        random_state=42, eval_metric='logloss'
    )
    heart_model.fit(X_train, y_train)
    
    accuracy = accuracy_score(y_test, heart_model.predict(X_test))
    print(f"   ✅ Accuracy: {accuracy * 100:.2f}%")
    
    with open("heart_model.pkl", "wb") as f:
        pickle.dump(heart_model, f)
    print(f"   💾 Saved: heart_model.pkl")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("📁 FILES CREATED:")
print("=" * 60)

for f in ["diabetes_model.pkl", "heart_model.pkl"]:
    if os.path.exists(f):
        size = os.path.getsize(f) / 1024
        print(f"   ✅ {f} ({size:.1f} KB)")
    else:
        print(f"   ❌ {f} (NOT FOUND)")

print("\n" + "=" * 60)
print("🎉 TRAINING COMPLETE!")
print("=" * 60) 