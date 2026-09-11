#AI Medical Report Analyzer & Health Risk Screening Platform
import streamlit as st
import fitz
import pandas as pd
import numpy as np
import re
import base64
from datetime import datetime
import plotly.express as px
import pickle
import os
import random

# ---------- VOICE & AI ----------
try:
    from streamlit_mic_recorder import speech_to_text
    VOICE_AVAILABLE = True
except:
    VOICE_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except:
    GROQ_AVAILABLE = False

# ---------- LOCAL MODULES ----------
import database as db
import ai_triage
import sms_service

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="MediScan Pro",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🔑 GROQ API KEY - YAHAN APNI NAYI KEY DAALO
# ============================================================
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

try:
    import streamlit as st
    if st.secrets.get("GROQ_API_KEY"):
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
except:
    pass  # ← YAHAN APNI KEY DAALO

# ---------- LOAD AI MODELS ----------
@st.cache_resource
def load_models():
    models = {"diabetes": None, "heart": None}
    try:
        if os.path.exists("diabetes_model.pkl"):
            with open("diabetes_model.pkl", "rb") as f:
                models["diabetes"] = pickle.load(f)
    except: pass
    try:
        if os.path.exists("heart_model.pkl"):
            with open("heart_model.pkl", "rb") as f:
                models["heart"] = pickle.load(f)
    except: pass
    return models

models = load_models()

# ---------- SESSION STATE ----------
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"
if 'logged_in_patient' not in st.session_state:
    st.session_state.logged_in_patient = None
if 'logged_in_doctor' not in st.session_state:
    st.session_state.logged_in_doctor = None
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background: #0a0a1a; }
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: 
            radial-gradient(ellipse at 20% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(139, 92, 246, 0.06) 0%, transparent 50%);
        animation: rotateBg 60s linear infinite;
        z-index: 0;
        pointer-events: none;
    }
    @keyframes rotateBg {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 4s ease-in-out infinite;
    }
    @keyframes gradientMove {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        letter-spacing: 2px;
    }
    
    .ios-card {
        background: rgba(20, 20, 50, 0.6);
        backdrop-filter: blur(30px);
        border-radius: 28px;
        padding: 2rem;
        margin: 1.2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    }
    
    .metric-card {
        background: linear-gradient(145deg, rgba(30, 30, 70, 0.6), rgba(15, 15, 40, 0.6));
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.04);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 12px 40px rgba(129, 140, 248, 0.2);
    }
    .metric-card h3 { font-size: 2.5rem; font-weight: 800; color: #e2e8f0; margin: 0; }
    .metric-card p { color: #94a3b8; margin: 0; font-size: 0.9rem; }
    .metric-card.green { background: linear-gradient(145deg, rgba(52, 211, 153, 0.12), rgba(16, 185, 129, 0.05)); }
    .metric-card.green h3 { color: #34d399; }
    .metric-card.red { background: linear-gradient(145deg, rgba(248, 113, 113, 0.12), rgba(239, 68, 68, 0.05)); }
    .metric-card.red h3 { color: #f87171; }
    .metric-card.cyan { background: linear-gradient(145deg, rgba(34, 211, 238, 0.12), rgba(6, 182, 212, 0.05)); }
    .metric-card.cyan h3 { color: #22d3ee; }
    .metric-card.orange { background: linear-gradient(145deg, rgba(251, 191, 36, 0.12), rgba(245, 158, 11, 0.05)); }
    .metric-card.orange h3 { color: #fbbf24; }
    .metric-card.purple { background: linear-gradient(145deg, rgba(167, 139, 250, 0.12), rgba(139, 92, 246, 0.05)); }
    .metric-card.purple h3 { color: #a78bfa; }
    
    .health-tip {
        background: linear-gradient(145deg, rgba(52, 211, 153, 0.08), rgba(16, 185, 129, 0.03));
        border-left: 4px solid #34d399;
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        margin: 0.5rem 0;
        color: #e2e8f0;
    }
    .health-tip-warning {
        background: linear-gradient(145deg, rgba(251, 191, 36, 0.08), rgba(245, 158, 11, 0.03));
        border-left-color: #fbbf24;
    }
    
    .bubble {
        display: inline-block;
        padding: 0.6rem 1.5rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 0.3rem;
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        color: white;
    }
    .bubble-red { background: linear-gradient(135deg, #f87171, #ef4444); }
    .bubble-green { background: linear-gradient(135deg, #34d399, #10b981); }
    
    .stButton > button {
        background: linear-gradient(135deg, #818cf8, #a78bfa) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.7rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.05) !important;
        box-shadow: 0 8px 24px rgba(129, 140, 248, 0.3) !important;
    }
    
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(15, 15, 40, 0.95), rgba(10, 10, 26, 0.98)) !important;
    }
    .css-1d391kg .stRadio label { color: #e2e8f0 !important; }
    
    .todo-item {
        padding: 0.7rem 1rem;
        background: rgba(129, 140, 248, 0.04);
        border-radius: 14px;
        margin: 0.4rem 0;
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    .tip-card {
        background: rgba(20, 20, 50, 0.4);
        padding: 0.9rem 1.2rem;
        border-radius: 16px;
        margin: 0.4rem 0;
        color: #e2e8f0;
        border-left: 4px solid #818cf8;
        font-size: 0.9rem;
    }
    
    .patient-info {
        background: linear-gradient(145deg, rgba(129, 140, 248, 0.1), rgba(167, 139, 250, 0.05));
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(129, 140, 248, 0.1);
        margin: 1rem 0;
    }
    .patient-info h3 { color: #818cf8; margin-bottom: 1rem; }
    .patient-info p { color: #e2e8f0; margin: 0.3rem 0; }
    
    .token-card {
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        border-radius: 24px;
        padding: 2rem;
        text-align: center;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 20px 60px rgba(129, 140, 248, 0.3);
    }
    .token-card h1 { font-size: 5rem; font-weight: 900; margin: 0; }
    .token-card p { font-size: 1.2rem; margin: 0.5rem 0 0 0; opacity: 0.9; }
    
    .doctor-card {
        background: linear-gradient(145deg, rgba(52, 211, 153, 0.1), rgba(16, 185, 129, 0.05));
        border-radius: 20px;
        padding: 1.5rem;
        border: 1px solid rgba(52, 211, 153, 0.2);
        margin: 0.5rem 0;
    }
    .doctor-card h3 { color: #34d399; margin: 0; }
    .doctor-card p { color: #e2e8f0; margin: 0.3rem 0; }
    
    .footer {
        text-align: center;
        padding: 1.5rem 0;
        color: #475569;
        border-top: 1px solid rgba(255, 255, 255, 0.03);
        margin-top: 2rem;
        font-size: 0.85rem;
    }
    
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(30, 30, 60, 0.3); }
    ::-webkit-scrollbar-thumb { background: #818cf8; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ---------- REFERENCE RANGES ----------
reference_ranges = {
    "Hemoglobin": {"min": 13.0, "max": 17.0, "unit": "g/dL", "category": "CBC"},
    "WBC": {"min": 4.0, "max": 11.0, "unit": "×10³/µL", "category": "CBC"},
    "Platelets": {"min": 150, "max": 450, "unit": "×10³/µL", "category": "CBC"},
    "Total Cholesterol": {"min": 125, "max": 200, "unit": "mg/dL", "category": "Lipid"},
    "Triglycerides": {"min": 0, "max": 150, "unit": "mg/dL", "category": "Lipid"},
    "HDL Cholesterol": {"min": 40, "max": 60, "unit": "mg/dL", "category": "Lipid"},
    "LDL Cholesterol": {"min": 0, "max": 130, "unit": "mg/dL", "category": "Lipid"},
    "Creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL", "category": "Renal"},
    "Uric Acid": {"min": 3.5, "max": 7.2, "unit": "mg/dL", "category": "Renal"},
    "TSH": {"min": 0.4, "max": 4.0, "unit": "µIU/mL", "category": "Thyroid"},
    "Fasting Glucose": {"min": 70, "max": 100, "unit": "mg/dL", "category": "Diabetes"},
    "HbA1c": {"min": 4.0, "max": 5.7, "unit": "%", "category": "Diabetes"},
    "SGOT (AST)": {"min": 10, "max": 40, "unit": "U/L", "category": "Liver"},
    "SGPT (ALT)": {"min": 10, "max": 40, "unit": "U/L", "category": "Liver"},
    "Total Bilirubin": {"min": 0.3, "max": 1.2, "unit": "mg/dL", "category": "Liver"},
    "Sodium": {"min": 136, "max": 145, "unit": "mEq/L", "category": "Renal"},
    "Potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L", "category": "Renal"},
    "Vitamin D": {"min": 30, "max": 100, "unit": "ng/mL", "category": "Vitamins"},
    "Vitamin B12": {"min": 200, "max": 900, "unit": "pg/mL", "category": "Vitamins"},
    "Ferritin": {"min": 20, "max": 500, "unit": "ng/mL", "category": "Iron"},
    "CRP": {"min": 0, "max": 5, "unit": "mg/L", "category": "Inflammatory"},
}

patterns = {
    "Hemoglobin": r"(?:Hb|Haemoglobin|Hemoglobin).*?(\d+\.?\d*)",
    "Glucose": r"(?:Glucose|Blood Sugar|Fasting).*?(\d+\.?\d*)",
    "WBC": r"(?:WBC|White Blood Cell).*?(\d+\.?\d*)",
    "Platelets": r"(?:Platelet|Thrombocyte).*?(\d+\.?\d*)",
    "Cholesterol": r"(?:Cholesterol|Total Cholesterol).*?(\d+\.?\d*)",
    "Creatinine": r"Creatinine.*?(\d+\.?\d*)",
    "TSH": r"TSH.*?(\d+\.?\d*)",
    "Uric Acid": r"Uric Acid.*?(\d+\.?\d*)",
    "Triglycerides": r"Triglycerides.*?(\d+\.?\d*)",
    "HDL Cholesterol": r"HDL.*?(\d+\.?\d*)",
    "LDL Cholesterol": r"LDL.*?(\d+\.?\d*)",
    "HbA1c": r"HbA1c.*?(\d+\.?\d*)",
    "SGOT": r"SGOT.*?(\d+\.?\d*)",
    "SGPT": r"SGPT.*?(\d+\.?\d*)",
    "Total Bilirubin": r"Total Bilirubin.*?(\d+\.?\d*)",
    "Sodium": r"Sodium.*?(\d+\.?\d*)",
    "Potassium": r"Potassium.*?(\d+\.?\d*)",
    "Vitamin D": r"Vitamin D.*?(\d+\.?\d*)",
    "Vitamin B12": r"Vitamin B12.*?(\d+\.?\d*)",
    "Ferritin": r"Ferritin.*?(\d+\.?\d*)",
    "CRP": r"CRP.*?(\d+\.?\d*)",
}

# ---------- HEALTH TIPS ----------
health_tips = [
    "🥗 Eat a balanced diet rich in fruits, vegetables, and whole grains",
    "💧 Drink at least 8 glasses of water daily",
    "🏃 Exercise for at least 30 minutes, 5 days a week",
    "😴 Get 7-8 hours of quality sleep every night",
    "🧘 Practice stress management through meditation or yoga",
    "🚭 Avoid smoking and limit alcohol consumption",
    "🩺 Schedule regular health check-ups",
    "🧠 Keep your brain active - read, learn, solve puzzles",
]

things_to_do = [
    "📋 Review your blood test results with your doctor",
    "📅 Schedule a follow-up appointment if needed",
    "🥗 Start incorporating healthier food choices",
    "🏃 Begin or maintain a regular exercise routine",
    "💊 Take prescribed medications on time",
    "📊 Track your daily health metrics",
]

# ---------- HELPER FUNCTIONS ----------
def get_download_link(df, filename="report.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}" style="text-decoration:none;color:#818cf8;font-weight:600;">📥 Download CSV Report</a>'

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

def predict_diabetes_risk(patient_data, report_data):
    if models["diabetes"] is None:
        return None
    try:
        glucose = 100
        for p in report_data:
            if "Glucose" in p["Parameter"]:
                glucose = p["Value"]
                break
        age = patient_data.get("age", 40)
        bp_str = str(patient_data.get("bp", "120/80"))
        bp = float(bp_str.split("/")[1]) if "/" in bp_str else 80
        input_data = np.array([[0, glucose, bp, 20, 100, 25.0, 0.5, age]])
        pred = models["diabetes"].predict(input_data)[0]
        prob = models["diabetes"].predict_proba(input_data)[0]
        return {"prediction": int(pred), "risk_percent": float(prob[1] * 100), "confidence": float(max(prob) * 100)}
    except:
        return None

def predict_heart_risk(patient_data, report_data):
    if models["heart"] is None:
        return None
    try:
        chol = 200
        for p in report_data:
            if "Cholesterol" in p["Parameter"]:
                chol = p["Value"]
                break
        age = patient_data.get("age", 50)
        gender = 1 if patient_data.get("gender", "Male") == "Male" else 0
        bp_str = str(patient_data.get("bp", "120/80"))
        bp = float(bp_str.split("/")[0]) if "/" in bp_str else 120
        input_data = np.array([[age, gender, 1, bp, chol, 1, 150, 0, 1.5, 2, 0, 2, 3]])
        pred = models["heart"].predict(input_data)[0]
        prob = models["heart"].predict_proba(input_data)[0]
        return {"prediction": int(pred), "risk_percent": float(prob[1] * 100), "confidence": float(max(prob) * 100)}
    except:
        return None

def ai_chat_response(question, report_data=None, patient_data=None):
    """AI Chatbot - login ke bina bhi kaam karega"""
    if not GROQ_AVAILABLE or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        return "⚠️ AI Chatbot setup nahi hua. Code mein Groq API key daalo."
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        if report_data and patient_data:
            report_summary = "\n".join([f"- {p['Parameter']}: {p['Value']} {p['Unit']} ({p['Status']})" for p in report_data])
            context = f"""You are a helpful medical assistant for MediScan Pro.
Patient: {patient_data.get('name')}, Age: {patient_data.get('age')}, Gender: {patient_data.get('gender')}
Patient's Report: {report_summary}
Patient's Conditions: {patient_data.get('conditions', 'None')}

Answer any health question the patient asks. Use their report data if relevant.
Rules: Simple patient-friendly language, no diagnosis, always recommend doctor, under 150 words."""
        else:
            context = """You are a helpful medical assistant for MediScan Pro.
The user is a guest and can ask ANY general health question.
Rules:
- Simple, patient-friendly language
- No diagnosis
- Always recommend consulting a doctor for medical decisions
- Under 150 words
- Be empathetic and helpful
- Answer general health, nutrition, exercise, mental health, first aid, etc."""
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question}
            ],
            temperature=0.4,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI error: {str(e)}"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.5rem 0;">
        <h2 style="color: #e2e8f0; margin: 0;">🩺 MediScan Pro</h2>
        <p style="color: #94a3b8; font-size: 0.8rem;">v5.0 • AI + Database</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.session_state.logged_in_patient:
        st.success(f"👤 Patient: {st.session_state.logged_in_patient['name']}")
    if st.session_state.logged_in_doctor:
        st.success(f"👨‍⚕️ Doctor: {st.session_state.logged_in_doctor['name']}")
    
    nav_items = []
    
    if st.session_state.logged_in_doctor:
        nav_items = [
            ("🏠 Home", "🏠 Home"),
            ("🩺 Doctor Dashboard", "🩺 Doctor Dashboard"),
            ("🚪 Logout", "🚪 Logout"),
        ]
    elif st.session_state.logged_in_patient:
        nav_items = [
            ("🏠 Home", "🏠 Home"),
            ("📤 Upload Report", "📤 Upload Report"),
            ("🎫 My Token", "🎫 My Token"),
            ("💊 My Prescriptions", "💊 My Prescriptions"),
            ("💬 AI Chatbot", "💬 AI Chatbot"),
            ("📜 My Reports", "📜 My Reports"),
            ("🚪 Logout", "🚪 Logout"),
        ]
    else:
      nav_items = [
        ("🏠 Home", "🏠 Home"),
        ("💬 AI Chatbot", "💬 AI Chatbot"),
        ("👤 Patient Register", "👤 Patient Register"),
        ("🔐 Patient Login", "🔐 Patient Login"),
        ("👨‍⚕️ Doctor Login", "👨‍⚕️ Doctor Login"),
        ("💡 Health Tips", "💡 Health Tips"),
        ("ℹ️ About", "ℹ️ About"),
    ]
    
    for label, target in nav_items:
        if st.button(label, use_container_width=True, key=f"nav_{target}"):
            if target == "🚪 Logout":
                st.session_state.logged_in_patient = None
                st.session_state.logged_in_doctor = None
                navigate_to("🏠 Home")
            else:
                navigate_to(target)
    
    st.divider()
    st.markdown("### 🤖 AI Status")
    st.markdown(f"{'✅' if models['diabetes'] else '❌'} Diabetes Model")
    st.markdown(f"{'✅' if models['heart'] else '❌'} Heart Model")
    st.markdown(f"{'✅' if GROQ_AVAILABLE and GROQ_API_KEY != 'YOUR_GROQ_API_KEY_HERE' else '❌'} AI Chatbot")

# ---------- MAIN ----------
st.markdown('<h1 class="main-title">🩺 MediScan Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Patient Case-Taking System</p>', unsafe_allow_html=True)

random_tip = random.choice(health_tips)
st.markdown(f'<div class="health-tip">💡 <b>Health Tip:</b> {random_tip}</div>', unsafe_allow_html=True)

page = st.session_state.page

# ============================================================
# PAGE: HOME
# ============================================================
if page == "🏠 Home":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    patients = db.get_all_patients()
    with col1:
        st.markdown(f'<div class="metric-card purple"><p>👥</p><h3>{len(patients)}</h3><p>Patients</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card green"><p>🤖</p><h3>2</h3><p>AI Models</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card cyan"><p>👨‍⚕️</p><h3>8</h3><p>Doctors</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card orange"><p>💾</p><h3>DB</h3><p>Saved</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    
    if not st.session_state.logged_in_patient and not st.session_state.logged_in_doctor:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-card purple"><p style="font-size:2rem;">👤</p><h3>Register</h3><p>New Patient</p></div>', unsafe_allow_html=True)
            if st.button("👤 Register Patient →", use_container_width=True, key="home_reg"):
                navigate_to("👤 Patient Register")
        with col2:
            st.markdown('<div class="metric-card green"><p style="font-size:2rem;">🔐</p><h3>Login</h3><p>Existing Patient</p></div>', unsafe_allow_html=True)
            if st.button("🔐 Patient Login →", use_container_width=True, key="home_pl"):
                navigate_to("🔐 Patient Login")
        with col3:
            st.markdown('<div class="metric-card cyan"><p style="font-size:2rem;">👨‍⚕️</p><h3>Doctor</h3><p>Login</p></div>', unsafe_allow_html=True)
            if st.button("👨‍⚕️ Doctor Login →", use_container_width=True, key="home_dl"):
                navigate_to("👨‍⚕️ Doctor Login")
    else:
        st.info("👈 Sidebar se navigate karo")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: PATIENT REGISTER
# ============================================================
elif page == "👤 Patient Register":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("👤 New Patient Registration")
    
    with st.form("register"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("👤 Full Name*")
            age = st.number_input("📅 Age*", 0, 120, 30)
        with col2:
            gender = st.selectbox("⚧️ Gender", ["Male", "Female", "Other"])
            phone = st.text_input("📞 Phone*")
        with col3:
            blood_group = st.selectbox("🩸 Blood Group", ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            email = st.text_input("📧 Email")
        
        st.divider()
        st.markdown("### 🔐 Login Credentials")
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username*", placeholder="Unique username")
        with col2:
            password = st.text_input("Password*", type="password")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            conditions = st.multiselect("Known Conditions",
                ["Diabetes", "Hypertension", "Heart Disease", "Asthma", "Thyroid", "Kidney Disease", "None"])
        with col2:
            allergies = st.multiselect("Allergies",
                ["Penicillin", "Sulfa", "Aspirin", "Latex", "Food - Nuts", "Food - Dairy", "None"])
        
        chief_complaint = st.text_area("📌 Chief Complaint*", height=80)
        
        st.subheader("🤒 Symptoms")
        col1, col2, col3 = st.columns(3)
        with col1:
            fever = st.checkbox("Fever")
            headache = st.checkbox("Headache")
        with col2:
            cough = st.checkbox("Cough")
            fatigue = st.checkbox("Fatigue")
        with col3:
            pain = st.checkbox("Pain")
            breath = st.checkbox("Shortness of Breath")
        
        symptoms = [s for s, v in {"Fever": fever, "Headache": headache, "Cough": cough,
                                    "Fatigue": fatigue, "Pain": pain, "Shortness of Breath": breath}.items() if v]
        
        st.subheader("📊 Vitals")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            bp_sys = st.number_input("BP Sys", 0, 300, 120)
        with col2:
            bp_dia = st.number_input("BP Dia", 0, 200, 80)
        with col3:
            pulse = st.number_input("Pulse", 0, 300, 72)
        with col4:
            temp = st.number_input("Temp °F", 0.0, 110.0, 98.6)
        
        submitted = st.form_submit_button("💾 Register Patient")
        
        if submitted:
            if not name or not chief_complaint or not username or not password:
                st.error("⚠️ Name, Chief Complaint, Username, Password required!")
            else:
                if db.get_patient_by_username(username):
                    st.error("❌ Username already exists!")
                else:
                    red_flags = ai_triage.check_red_flags(chief_complaint + " " + " ".join(symptoms))
                    
                    patient_data = {
                        "name": name, "age": age, "gender": gender, "phone": phone,
                        "email": email, "blood_group": blood_group,
                        "conditions": ", ".join(conditions) if conditions else "None",
                        "allergies": ", ".join(allergies) if allergies else "None",
                        "chief_complaint": chief_complaint,
                        "symptoms": ", ".join(symptoms) if symptoms else "None",
                        "bp": f"{bp_sys}/{bp_dia}", "pulse": pulse, "temperature": temp,
                        "red_flags": red_flags,
                        "username": username, "password": password
                    }
                    
                    patient_id = db.save_patient(patient_data)
                    
                    try:
                        sms_service.send_sms(patient_id, phone, f"Welcome {name}! Aapka MediScan Pro account ban gaya hai. Username: {username}")
                    except: pass
                    
                    st.success(f"✅ Patient registered! ID: {patient_id}")
                    st.info(f"📌 Username: **{username}** — Ab login karo!")
                    st.balloons()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: PATIENT LOGIN
# ============================================================
elif page == "🔐 Patient Login":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("🔐 Patient Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("patient_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submitted:
                patient = db.get_patient_by_username(username)
                if patient and patient['password'] == password:
                    st.session_state.logged_in_patient = patient
                    st.success(f"✅ Welcome {patient['name']}!")
                    st.balloons()
                    navigate_to("📤 Upload Report")
                else:
                    st.error("❌ Invalid username or password!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: DOCTOR LOGIN
# ============================================================
elif page == "👨‍⚕️ Doctor Login":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("👨‍⚕️ Doctor Login")
    
    st.info("**Demo Login Credentials:**")
    st.code("""
Username: dr.sharma   Password: doctor123
Username: dr.verma    Password: doctor123
Username: dr.gupta    Password: doctor123
Username: dr.singh    Password: doctor123
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("doctor_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submitted:
                doctor = db.get_doctor_by_username(username)
                if doctor and doctor['password'] == password:
                    st.session_state.logged_in_doctor = doctor
                    st.success(f"✅ Welcome {doctor['name']}!")
                    st.balloons()
                    navigate_to("🩺 Doctor Dashboard")
                else:
                    st.error("❌ Invalid username or password!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: UPLOAD REPORT
# ============================================================
elif page == "📤 Upload Report":
    if not st.session_state.logged_in_patient:
        st.warning("⚠️ Pehle login karo!")
        if st.button("🔐 Login"):
            navigate_to("🔐 Patient Login")
    else:
        patient = st.session_state.logged_in_patient
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader(f"📤 Upload Report for {patient['name']}")
        
        uploaded_file = st.file_uploader("Choose PDF", type=["pdf"])
        
        if uploaded_file:
            with st.spinner("🔍 Extracting..."):
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = "".join([p.get_text() for p in doc])
            
            found_params = []
            for param, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    range_info = reference_ranges.get(param, {})
                    if range_info:
                        min_val = range_info.get("min", 0)
                        max_val = range_info.get("max", 0)
                        unit = range_info.get("unit", "N/A")
                        category = range_info.get("category", "General")
                        if value < min_val: status = "🔴 LOW"
                        elif value > max_val: status = "🔴 HIGH"
                        else: status = "🟢 NORMAL"
                    else:
                        status, unit, category = "⚠️ CHECK", "N/A", "General"
                    
                    found_params.append({
                        "Parameter": param, "Value": value, "Unit": unit,
                        "Category": category, "Status": status
                    })
            
            st.session_state.current_results = found_params
            
            if found_params:
                st.success("✅ Report analyzed!")
                df = pd.DataFrame(found_params)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                try:
                    db.save_report(patient['patient_id'], uploaded_file.name, found_params)
                except: pass
                
                st.markdown("---")
                st.markdown("### 🤖 AI Risk Screening")
                col1, col2 = st.columns(2)
                
                with col1:
                    diab = predict_diabetes_risk(patient, found_params)
                    if diab:
                        color = "red" if diab['prediction'] == 1 else "green"
                        st.markdown(f'<div class="metric-card {color}"><p>🩸 Diabetes Risk</p><h3>{diab["risk_percent"]:.1f}%</h3><p>{"⚠️ HIGH" if diab["prediction"] == 1 else "✅ LOW"}</p></div>', unsafe_allow_html=True)
                    else:
                        st.info("🩸 Diabetes model load nahi hua")
                
                with col2:
                    heart = predict_heart_risk(patient, found_params)
                    if heart:
                        color = "red" if heart['prediction'] == 1 else "green"
                        st.markdown(f'<div class="metric-card {color}"><p>❤️ Heart Risk</p><h3>{heart["risk_percent"]:.1f}%</h3><p>{"⚠️ HIGH" if heart["prediction"] == 1 else "✅ LOW"}</p></div>', unsafe_allow_html=True)
                    else:
                        st.info("❤️ Heart model load nahi hua")
                
                st.markdown("---")
                st.markdown("### 🩺 AI Specialist Assignment")
                
                triage = ai_triage.triage_patient(
                    patient.get('symptoms', ''),
                    patient.get('age', 30),
                    patient.get('gender', 'Male'),
                    patient.get('chief_complaint', '')
                )
                
                st.markdown(f"""
                <div class="doctor-card">
                    <h3>👨‍⚕️ Recommended: {triage['specialist']}</h3>
                    <p>Confidence: {triage['confidence']}%</p>
                    <p>Urgency: {triage['urgency']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if triage['red_flags']:
                    st.error(f"🚨 RED FLAGS: {', '.join(triage['red_flags'])}")
                
                st.markdown("---")
                if st.button("📅 Book Appointment", use_container_width=True):
                    doctors = db.get_doctors_by_specialist(triage['specialist'])
                    if not doctors:
                        doctors = db.get_doctors_by_specialist("General Physician")
                    
                    if doctors:
                        doctor = doctors[0]
                        slot_time = datetime.now().strftime("%I:%M %p")
                        
                        appt_id, token = db.create_appointment(
                            patient['patient_id'], doctor['doctor_id'],
                            triage['specialist'], slot_time
                        )
                        
                        try:
                            sms_service.send_appointment_confirmation(
                                patient['patient_id'], patient['phone'],
                                patient['name'], doctor['name'],
                                triage['specialist'], token, slot_time,
                                datetime.now().strftime("%d/%m/%Y")
                            )
                        except: pass
                        
                        st.success(f"✅ Appointment booked! Token: {token}")
                        st.balloons()
                    else:
                        st.error("❌ No doctors available!")
                
                st.markdown(get_download_link(df), unsafe_allow_html=True)
            else:
                st.warning("No parameters detected.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: MY TOKEN
# ============================================================
elif page == "🎫 My Token":
    if not st.session_state.logged_in_patient:
        st.warning("⚠️ Pehle login karo!")
    else:
        patient = st.session_state.logged_in_patient
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader("🎫 My Appointments")
        
        appointments = db.get_appointments_by_patient(patient['patient_id'])
        
        if not appointments:
            st.info("📭 No appointments booked yet. Upload a report first!")
        else:
            for appt in appointments:
                st.markdown(f"""
                <div class="token-card">
                    <p>Token Number</p>
                    <h1>{appt['token_number']}</h1>
                    <p>👨‍⚕️ {appt['doctor_name']} ({appt['doctor_specialist']})</p>
                    <p>⏰ {appt['slot_time']} • 📅 {appt['appointment_date']}</p>
                    <p>Status: {appt['status']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                wait = ai_triage.estimate_wait_time(appt['token_number'])
                st.info(f"⏳ Estimated Wait Time: **{wait}**")
                st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: MY PRESCRIPTIONS
# ============================================================
elif page == "💊 My Prescriptions":
    if not st.session_state.logged_in_patient:
        st.warning("⚠️ Pehle login karo!")
    else:
        patient = st.session_state.logged_in_patient
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader("💊 My Prescriptions")
        
        prescriptions = db.get_prescriptions_by_patient(patient['patient_id'])
        
        if not prescriptions:
            st.info("📭 No prescriptions yet.")
        else:
            for presc in prescriptions:
                st.markdown(f"""
                <div class="patient-info">
                    <h3>💊 Prescription #{presc['prescription_id']}</h3>
                    <p><b>Doctor:</b> {presc['doctor_name']}</p>
                    <p><b>Date:</b> {presc['created_at']}</p>
                    <p><b>Diagnosis:</b> {presc['diagnosis']}</p>
                    <p><b>Medicines:</b> {presc['medicines']}</p>
                    <p><b>Advice:</b> {presc['advice']}</p>
                    <p><b>Follow-up:</b> {presc['follow_up_date']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: AI CHATBOT
# ============================================================
# ============================================================
# PAGE: AI CHATBOT
# ============================================================
elif page == "💬 AI Chatbot":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("💬 AI Health Assistant")
    
    if st.session_state.logged_in_patient:
        st.success(f"👤 Logged in as: {st.session_state.logged_in_patient['name']}")
        st.caption("Report + general health questions — dono pooch sakte ho!")
    else:
        st.info("👋 Welcome! Koi bhi health sawaal pooch sakte ho.")
        st.caption("💡 Report-specific answers ke liye patient login karo.")
    
    st.markdown("**Quick Questions:**")
    col1, col2, col3, col4 = st.columns(4)
    quick_q = None
    with col1:
        if st.button("💧 Paani", use_container_width=True):
            quick_q = "Din mein kitna paani peena chahiye?"
    with col2:
        if st.button("😴 Neend", use_container_width=True):
            quick_q = "Healthy neend ke liye tips batao"
    with col3:
        if st.button("🏃 Exercise", use_container_width=True):
            quick_q = "Roz kitna exercise karna chahiye?"
    with col4:
        if st.button("🥗 Diet", use_container_width=True):
            quick_q = "Healthy diet kya hoti hai?"
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(chat["q"])
        with st.chat_message("assistant"):
            st.write(chat["a"])
    
    user_q = st.chat_input("Kuch bhi poocho...")
    final_q = quick_q or user_q
    
    if final_q:
        with st.chat_message("user"):
            st.write(final_q)
        with st.chat_message("assistant"):
            with st.spinner("🤔..."):
                if st.session_state.logged_in_patient:
                    patient = st.session_state.logged_in_patient
                    reports = db.get_patient_reports(patient['patient_id'])
                    report_data = reports[0]['parameters'] if reports else []
                    answer = ai_chat_response(final_q, report_data, patient)
                else:
                    answer = ai_chat_response(final_q)
                st.write(answer)
        st.session_state.chat_history.append({"q": final_q, "a": answer})
    
    st.markdown('</div>', unsafe_allow_html=True)
# ============================================================
# PAGE: MY REPORTS
# ============================================================
elif page == "📜 My Reports":
    if not st.session_state.logged_in_patient:
        st.warning("⚠️ Pehle login karo!")
    else:
        patient = st.session_state.logged_in_patient
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader("📜 My Reports")
        
        reports = db.get_patient_reports(patient['patient_id'])
        
        if not reports:
            st.info("📭 No reports yet.")
        else:
            for r in reports:
                with st.expander(f"📄 {r['filename']} — {r['uploaded_at']}"):
                    df = pd.DataFrame(r['parameters'])
                    st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: DOCTOR DASHBOARD
# ============================================================
elif page == "🩺 Doctor Dashboard":
    if not st.session_state.logged_in_doctor:
        st.warning("⚠️ Pehle doctor login karo!")
    else:
        doctor = st.session_state.logged_in_doctor
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader(f"🩺 Welcome {doctor['name']}")
        st.caption(f"{doctor['specialist']} • {doctor['qualification']}")
        
        appointments = db.get_appointments_by_doctor(doctor['doctor_id'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card purple"><p>📅 Today</p><h3>{len(appointments)}</h3></div>', unsafe_allow_html=True)
        with col2:
            waiting = sum(1 for a in appointments if a['status'] == 'Waiting')
            st.markdown(f'<div class="metric-card orange"><p>⏳ Waiting</p><h3>{waiting}</h3></div>', unsafe_allow_html=True)
        with col3:
            done = sum(1 for a in appointments if a['status'] == 'Completed')
            st.markdown(f'<div class="metric-card green"><p>✅ Done</p><h3>{done}</h3></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📋 Today's Patients")
        
        if not appointments:
            st.info("📭 No appointments today.")
        else:
            for appt in appointments:
                with st.expander(f"🎫 Token {appt['token_number']} — {appt['patient_name']} ({appt['patient_age']}y) — {appt['status']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📌 Chief Complaint:** {appt['chief_complaint']}")
                        st.markdown(f"**🤒 Symptoms:** {appt['symptoms']}")
                    with col2:
                        reports = db.get_patient_reports(appt['patient_id'])
                        if reports:
                            st.markdown(f"**📄 Reports:** {len(reports)}")
                            df = pd.DataFrame(reports[0]['parameters'])
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if appt['status'] == 'Waiting':
                            if st.button("▶️ Start", key=f"start_{appt['appointment_id']}"):
                                db.update_appointment_status(appt['appointment_id'], 'In Consultation')
                                st.rerun()
                    with col2:
                        if appt['status'] == 'In Consultation':
                            if st.button("✅ Complete", key=f"done_{appt['appointment_id']}"):
                                db.update_appointment_status(appt['appointment_id'], 'Completed')
                                st.rerun()
                    
                    if appt['status'] == 'In Consultation':
                        st.markdown("#### 💊 Prescription")
                        with st.form(f"presc_{appt['appointment_id']}"):
                            diagnosis = st.text_input("Diagnosis")
                            medicines = st.text_area("Medicines")
                            advice = st.text_area("Advice")
                            follow_up = st.date_input("Follow-up Date")
                            
                            if st.form_submit_button("💾 Save"):
                                db.save_prescription(
                                    appt['appointment_id'], appt['patient_id'],
                                    doctor['doctor_id'], diagnosis, medicines,
                                    advice, str(follow_up)
                                )
                                try:
                                    patient = db.get_patient(appt['patient_id'])
                                    if patient:
                                        sms_service.send_prescription_ready(
                                            appt['patient_id'], patient['phone'],
                                            patient['name'], doctor['name'], diagnosis
                                        )
                                except: pass
                                st.success("✅ Prescription saved!")
                                st.balloons()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: HEALTH TIPS
# ============================================================
elif page == "💡 Health Tips":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("💡 Health Tips")
    cols = st.columns(3)
    for idx, tip in enumerate(health_tips):
        with cols[idx % 3]:
            st.markdown(f'<div class="tip-card">{tip}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: ABOUT
# ============================================================
elif page == "ℹ️ About":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader("ℹ️ About MediScan Pro v5.0")
    st.markdown("""
    **AI-Powered Patient Case-Taking & Hospital Management System**
    
    #### Features:
    - 👤 Patient Registration + Login
    - 🔐 Patient Login
    - 👨‍⚕️ Doctor Login
    - 📤 Report Upload + AI Analysis
    - 🤖 XGBoost Risk Prediction (Diabetes + Heart)
    - 💬 Groq AI Chatbot
    - 🎫 Token Generation
    - 👨‍⚕️ AI Specialist Assignment
    - 💊 Online Prescription
    - 📱 SMS Notifications
    - 🩺 Doctor Dashboard
    - 📜 Patient History
    
    ⚠️ **Disclaimer:** Screening tool only. Consult doctor.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    <p>🩺 MediScan Pro v5.0 • AI + Database + Hospital Management</p>
    <p style="font-size:0.7rem;">⚠️ Demo • Not for diagnostic use</p>
</div>
""", unsafe_allow_html=True)