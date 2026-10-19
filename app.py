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
import json
from fpdf import FPDF

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
import completeness_engine
import security

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="MediScan Pro", page_icon="🩺", layout="wide", initial_sidebar_state="expanded")

# ---------- API KEY SETUP ----------
try: GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
except: GROQ_API_KEY = ""

# ---------- LOAD AI MODELS ----------
@st.cache_resource
def load_models():
    models = {"diabetes": None, "heart": None}
    try:
        if os.path.exists("diabetes_model.pkl"):
            with open("diabetes_model.pkl", "rb") as f: models["diabetes"] = pickle.load(f)
    except: pass
    try:
        if os.path.exists("heart_model.pkl"):
            with open("heart_model.pkl", "rb") as f: models["heart"] = pickle.load(f)
    except: pass
    return models
models = load_models()

# ---------- MULTILINGUAL DICTIONARY ----------
TEXT = {
    "English": {
        "home": "🏠 Home", "patient_reg": "👤 Patient Register", "patient_login": "🔐 Patient Login",
        "doc_login": "👨‍⚕️ Doctor Login", "doc_dash": "🩺 Doctor Dashboard", "chatbot": "💬 AI Chatbot",
        "about": "ℹ️ About", "logout": "🚪 Logout", "sys_title": "AI-Powered Patient Case-Taking System",
        "name": "Full Name*", "age": "Age*", "gender": "Gender", "phone": "Phone*", "blood": "Blood Group",
        "user": "Username*", "pass": "Password*", "complaint": "Chief Complaint*", "ayush": "🕉️ AYUSH Assessment (Optional)",
        "prakriti": "Prakriti", "agni": "Agni (Digestion)", "koshtha": "Koshtha (Bowel)", "vitals": "Vitals",
        "register_btn": "💾 Register Patient", "login_btn": "🔐 Login", "upload_pdf": "Upload PDF Report",
        "analyzing": "🔍 Analyzing...", "save": "💾 Save", "view_pdf": "📄 Original Report",
        "notes": "📝 Doctor's Notes", "presc": "💊 Prescription", "diagnosis": "Diagnosis", "meds": "Medicines",
        "download_pdf": "📥 Download Prescription PDF"
    },
    "Hindi": {
        "home": "🏠 होम", "patient_reg": "👤 मरीज़ रजिस्टर", "patient_login": "🔐 मरीज़ लॉगिन",
        "doc_login": "👨‍⚕️ डॉक्टर लॉगिन", "doc_dash": "🩺 डॉक्टर डैशबोर्ड", "chatbot": "💬 एआई चैटबॉट",
        "about": "ℹ️ ऐप के बारे में", "logout": "🚪 लॉगआउट", "sys_title": "एआई-आधारित मरीज़ केस-टेकिंग सिस्टम",
        "name": "पूरा नाम*", "age": "उम्र*", "gender": "लिंग", "phone": "फ़ोन नंबर*", "blood": "ब्लड ग्रुप",
        "user": "यूज़रनेम*", "pass": "पासवर्ड*", "complaint": "मुख्य शिकायत*", "ayush": "🕉️ आयुष मूल्यांकन (वैकल्पिक)",
        "prakriti": "प्रकृति", "agni": "अग्नि (पाचन)", "koshtha": "कोष्ठ (पेट)", "vitals": "बुनियादी स्वास्थ्य जांच",
        "register_btn": "💾 मरीज़ रजिस्टर करें", "login_btn": "🔐 लॉगिन करें", "upload_pdf": "रिपोर्ट अपलोड करें",
        "analyzing": "🔍 जांच हो रही है...", "save": "💾 सेव करें", "view_pdf": "📄 मूल रिपोर्ट",
        "notes": "📝 डॉक्टर के नोट्स", "presc": "💊 पर्चा (दवाइयां)", "diagnosis": "बीमारी का नाम", "meds": "दवाइयां",
        "download_pdf": "📥 पर्चा डाउनलोड करें"
    }
}

# ---------- SESSION STATE ----------
if 'page' not in st.session_state: st.session_state.page = "🏠 Home"
if 'language' not in st.session_state: st.session_state.language = "English"
if 'logged_in_patient' not in st.session_state: st.session_state.logged_in_patient = None
if 'logged_in_doctor' not in st.session_state: st.session_state.logged_in_doctor = None
if 'current_results' not in st.session_state: st.session_state.current_results = None
if 'chat' not in st.session_state: st.session_state.chat = []

T = TEXT[st.session_state.language]

# ---------- CUSTOM CSS (3D Premium UI) ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { 
        background: radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.15), transparent 25%),
                    radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15), transparent 25%),
                    #0a0a1a; 
    }
    
    .main-title { 
        font-size: 4rem; font-weight: 900; text-align: center; 
        background: linear-gradient(135deg, #a78bfa, #818cf8, #c084fc, #818cf8); 
        background-size: 300% 300%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        animation: gradientMove 5s ease-in-out infinite; text-shadow: 0px 0px 30px rgba(129, 140, 248, 0.3);
    }
    @keyframes gradientMove { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
    
    .subtitle { text-align: center; color: #94a3b8; font-size: 1.2rem; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 2rem; }
    .ios-card { background: rgba(20, 20, 50, 0.6); backdrop-filter: blur(30px); border-radius: 28px; padding: 2rem; margin: 1.2rem 0; border: 1px solid rgba(255, 255, 255, 0.06); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4); }
    
    .card-3d { 
        background: rgba(30, 30, 70, 0.4); backdrop-filter: blur(20px); border-radius: 24px; padding: 2rem; text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1); 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); transform: perspective(1000px) rotateX(5deg) translateY(0);
    }
    .card-3d:hover { transform: perspective(1000px) rotateX(0deg) translateY(-10px) scale(1.02); box-shadow: 0 30px 60px rgba(129, 140, 248, 0.2), inset 0 1px 0 rgba(255,255,255,0.2); border-color: rgba(129, 140, 248, 0.4); }
    .card-3d h3 { font-size: 3rem; font-weight: 800; margin: 0; color: #fff; text-shadow: 0 0 20px rgba(255,255,255,0.3); }
    .card-3d p { color: #a78bfa; margin-top: 10px; font-size: 1rem; font-weight: 600; letter-spacing: 1px; }
    
    .health-tip { background: linear-gradient(90deg, rgba(52, 211, 153, 0.1), transparent); border-left: 4px solid #34d399; padding: 1rem 1.5rem; border-radius: 8px; color: #e2e8f0; font-weight: 500; }
    .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 50px !important; padding: 0.8rem 2rem !important; font-weight: 700 !important; box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3) !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { transform: translateY(-3px) scale(1.02) !important; box-shadow: 0 15px 30px rgba(99, 102, 241, 0.5) !important; }
    
    .patient-info { background: linear-gradient(145deg, rgba(129, 140, 248, 0.1), rgba(167, 139, 250, 0.05)); border-radius: 20px; padding: 1.5rem; border: 1px solid rgba(129, 140, 248, 0.1); margin: 1rem 0; }
    .token-card { background: linear-gradient(135deg, #818cf8, #a78bfa); border-radius: 24px; padding: 2rem; text-align: center; color: white; margin: 1rem 0; }
    .token-card h1 { font-size: 5rem; font-weight: 900; margin: 0; }
    .footer { text-align: center; padding: 1.5rem 0; color: #475569; margin-top: 3rem; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------- CONFIGURATIONS ----------
reference_ranges = {"Hemoglobin": {"min": 13.0, "max": 17.0, "unit": "g/dL"}, "WBC": {"min": 4.0, "max": 11.0, "unit": "×10³/µL"}, "Platelets": {"min": 150, "max": 450, "unit": "×10³/µL"}, "Total Cholesterol": {"min": 125, "max": 200, "unit": "mg/dL"}, "Triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"}, "HDL Cholesterol": {"min": 40, "max": 60, "unit": "mg/dL"}, "LDL Cholesterol": {"min": 0, "max": 130, "unit": "mg/dL"}, "Creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL"}, "Uric Acid": {"min": 3.5, "max": 7.2, "unit": "mg/dL"}, "TSH": {"min": 0.4, "max": 4.0, "unit": "µIU/mL"}, "Fasting Glucose": {"min": 70, "max": 100, "unit": "mg/dL"}, "HbA1c": {"min": 4.0, "max": 5.7, "unit": "%"}, "SGOT (AST)": {"min": 10, "max": 40, "unit": "U/L"}, "SGPT (ALT)": {"min": 10, "max": 40, "unit": "U/L"}}
patterns = {"Hemoglobin": r"(?:Hb|Haemoglobin|Hemoglobin).*?(\d+\.?\d*)", "Glucose": r"(?:Glucose|Blood Sugar|Fasting).*?(\d+\.?\d*)", "WBC": r"(?:WBC|White Blood Cell).*?(\d+\.?\d*)", "Platelets": r"(?:Platelet|Thrombocyte).*?(\d+\.?\d*)", "Cholesterol": r"(?:Cholesterol|Total Cholesterol).*?(\d+\.?\d*)", "Creatinine": r"Creatinine.*?(\d+\.?\d*)", "TSH": r"TSH.*?(\d+\.?\d*)", "Uric Acid": r"Uric Acid.*?(\d+\.?\d*)", "SGOT": r"SGOT.*?(\d+\.?\d*)", "SGPT": r"SGPT.*?(\d+\.?\d*)"}
health_tips = ["🥗 Eat a balanced diet", "💧 Drink 8 glasses of water", "🏃 Exercise 30 mins daily", "😴 Get 7-8 hours sleep"]

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ---------- HELPER FUNCTIONS ----------
def predict_diabetes_risk(patient_data, report_data):
    if models["diabetes"] is None: return None
    try:
        glucose = next((p["Value"] for p in report_data if "Glucose" in p["Parameter"]), 100)
        bp = float(str(patient_data.get("bp", "120/80")).split("/")[1]) if "/" in str(patient_data.get("bp")) else 80
        input_data = np.array([[0, glucose, bp, 20, 100, 25.0, 0.5, patient_data.get("age", 40)]])
        prob = models["diabetes"].predict_proba(input_data)[0]
        return {"prediction": int(models["diabetes"].predict(input_data)[0]), "risk_percent": float(prob[1] * 100)}
    except: return None

def predict_heart_risk(patient_data, report_data):
    if models["heart"] is None: return None
    try:
        chol = next((p["Value"] for p in report_data if "Cholesterol" in p["Parameter"]), 200)
        bp = float(str(patient_data.get("bp", "120/80")).split("/")[0]) if "/" in str(patient_data.get("bp")) else 120
        input_data = np.array([[patient_data.get("age", 50), 1 if patient_data.get("gender")=="Male" else 0, 1, bp, chol, 1, 150, 0, 1.5, 2, 0, 2, 3]])
        prob = models["heart"].predict_proba(input_data)[0]
        return {"prediction": int(models["heart"].predict(input_data)[0]), "risk_percent": float(prob[1] * 100)}
    except: return None

def ai_chat_response(question, report_data=None, patient_data=None):
    if not GROQ_AVAILABLE or not GROQ_API_KEY: return "⚠️ AI setup pending."
    try:
        client = Groq(api_key=GROQ_API_KEY)
        context = "You are a helpful medical assistant. Answer simply. No diagnosis."
        if report_data and patient_data: context += f"\nPatient: {patient_data.get('name')}. Report: {report_data}"
        response = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role": "system", "content": context}, {"role": "user", "content": question}], max_tokens=300)
        return response.choices[0].message.content
    except: return "Error connecting to AI."

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color: #e2e8f0;'>🩺 MediScan Pro</h2>", unsafe_allow_html=True)
    
    lang_options = ["English", "Hindi"]
    selected_lang = st.selectbox("🌐 Language / भाषा", lang_options, index=lang_options.index(st.session_state.language))
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()
        
    st.divider()
    if st.session_state.logged_in_patient: st.success(f"👤 {st.session_state.logged_in_patient['name']}")
    if st.session_state.logged_in_doctor: st.success(f"👨‍⚕️ {st.session_state.logged_in_doctor['name']}")
    
    nav_items = []
    if st.session_state.logged_in_doctor: 
        nav_items = [(T["home"], "🏠 Home"), (T["doc_dash"], "🩺 Doctor Dashboard"), (T["about"], "ℹ️ About"), (T["logout"], "🚪 Logout")]
    elif st.session_state.logged_in_patient: 
        nav_items = [(T["home"], "🏠 Home"), (T["upload_pdf"], "📤 Upload Report"), ("🎫 My Token", "🎫 My Token"), ("💊 My Prescriptions", "💊 My Prescriptions"), (T["chatbot"], "💬 AI Chatbot"), (T["about"], "ℹ️ About"), (T["logout"], "🚪 Logout")]
    else: 
        nav_items = [(T["home"], "🏠 Home"), (T["chatbot"], "💬 AI Chatbot"), (T["patient_reg"], "👤 Patient Register"), (T["patient_login"], "🔐 Patient Login"), (T["doc_login"], "👨‍⚕️ Doctor Login"), (T["about"], "ℹ️ About")]
    
    for label, target in nav_items:
        if st.button(label, use_container_width=True, key=f"nav_{target}"):
            if target == "🚪 Logout":
                st.session_state.logged_in_patient = None
                st.session_state.logged_in_doctor = None
                navigate_to("🏠 Home")
            else: navigate_to(target)

# ---------- MAIN UI ----------
page = st.session_state.page

# ============================================================
# PAGE: HOME (3D Visualisation)
# ============================================================
if page == "🏠 Home":
    st.markdown('<h1 class="main-title">🩺 MediScan Pro</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{T["sys_title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="health-tip">💡 <b>Health Tip:</b> {random.choice(health_tips)}</div><br>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="card-3d"><p>👥</p><h3>Live</h3><p>Active Patients</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="card-3d"><p>🤖</p><h3>2</h3><p>ML Risk Models</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="card-3d"><p>👨‍⚕️</p><h3>8</h3><p>Specialist Doctors</p></div>', unsafe_allow_html=True)

    st.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)

    col_organs, col_action = st.columns([2, 1])
    
    with col_organs:
        st.markdown("### 🫀 Internal Organ Health Insights")
        st.caption("AI-powered real-time analysis of vital organs")
        
        # Heart Card
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(248, 113, 113, 0.1), rgba(239, 68, 68, 0.05)); border-radius: 20px; padding: 1.5rem; margin-bottom: 15px; border-left: 5px solid #f87171; box-shadow: 0 10px 30px rgba(248, 113, 113, 0.1); transition: all 0.3s ease;">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 3.5rem; margin-right: 20px; filter: drop-shadow(0px 10px 10px rgba(248,113,113,0.5));">❤️</div>
                <div>
                    <h4 style="margin: 0; color: #f87171;">Cardiovascular System (Heart)</h4>
                    <ul style="margin-top: 10px; color: #cbd5e1; font-size: 0.95rem; padding-left: 15px;">
                        <li><b>Risk Prediction:</b> AI screens for Heart Disease risk using XGBoost model based on Cholesterol & BP.</li>
                        <li><b>Vitals Tracking:</b> Monitors blood pressure and pulse rate to detect early signs of hypertension.</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Lungs/Brain Card
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(251, 191, 36, 0.1), rgba(245, 158, 11, 0.05)); border-radius: 20px; padding: 1.5rem; margin-bottom: 15px; border-left: 5px solid #fbbf24; box-shadow: 0 10px 30px rgba(251, 191, 36, 0.1); transition: all 0.3s ease;">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 3.5rem; margin-right: 20px; filter: drop-shadow(0px 10px 10px rgba(251,191,36,0.5));">🧠</div>
                <div>
                    <h4 style="margin: 0; color: #fbbf24;">Neurological System (Brain)</h4>
                    <ul style="margin-top: 10px; color: #cbd5e1; font-size: 0.95rem; padding-left: 15px;">
                        <li><b>Symptom Triage:</b> AI Triage routes headaches, dizziness, and memory loss to Neurologists.</li>
                        <li><b>Red Flag Detection:</b> Instantly alerts doctors for emergency symptoms like paralysis or seizures.</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Kidney Card
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(34, 211, 238, 0.1), rgba(6, 182, 212, 0.05)); border-radius: 20px; padding: 1.5rem; margin-bottom: 15px; border-left: 5px solid #22d3ee; box-shadow: 0 10px 30px rgba(34, 211, 238, 0.1); transition: all 0.3s ease;">
            <div style="display: flex; align-items: center;">
                <div style="font-size: 3.5rem; margin-right: 20px; filter: drop-shadow(0px 10px 10px rgba(34,211,238,0.5));">🫘</div>
                <div>
                    <h4 style="margin: 0; color: #22d3ee;">Renal System (Kidneys)</h4>
                    <ul style="margin-top: 10px; color: #cbd5e1; font-size: 0.95rem; padding-left: 15px;">
                        <li><b>Filtration Rate:</b> Monitors Blood Urea and Creatinine to assess kidney function.</li>
                        <li><b>Electrolyte Balance:</b> Tracks Sodium and Potassium levels, crucial for nerve and muscle function.</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_action:
        st.markdown("### ⚡ Quick Actions")
        st.write("Get started with MediScan Pro")
        st.write("")
        if not st.session_state.logged_in_patient and not st.session_state.logged_in_doctor:
            if st.button(T["patient_reg"], use_container_width=True): navigate_to("👤 Patient Register")
            st.write("")
            if st.button(T["patient_login"], use_container_width=True): navigate_to("🔐 Patient Login")
            st.write("")
            if st.button(T["doc_login"], use_container_width=True): navigate_to("👨‍⚕️ Doctor Login")
        else:
            st.success("✅ You are logged in.")
            if st.button("Go to Dashboard", use_container_width=True):
                if st.session_state.logged_in_doctor: navigate_to("🩺 Doctor Dashboard")
                else: navigate_to("📤 Upload Report")

# ============================================================
# PAGE: PATIENT REGISTER (Voice + Ayurveda)
# ============================================================
elif page == "👤 Patient Register":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    with st.form("register"):
        c1, c2, c3 = st.columns(3)
        with c1: name = st.text_input(T["name"]); age = st.number_input(T["age"], 0, 120, 30)
        with c2: gender = st.selectbox(T["gender"], ["Male", "Female", "Other"]); phone = st.text_input(T["phone"])
        with c3: blood_group = st.selectbox(T["blood"], ["", "A+", "B+", "O+", "AB+"]); email = st.text_input("📧 Email")
        
        st.markdown("### 🔐 Login Credentials")
        c1, c2 = st.columns(2)
        with c1: username = st.text_input(T["user"])
        with c2: password = st.text_input(T["pass"], type="password")
        
        st.markdown(f"### 📌 {T['complaint']}")
        if VOICE_AVAILABLE:
            st.info("Aap bolkar bhi apni problem bata sakte hain:")
            voice_text = speech_to_text(language='en', start_prompt="🎤 Record Complaint", stop_prompt="🛑 Stop", just_once=True, key='voice_comp')
            if voice_text:
                st.success(f"Recorded: {voice_text}")
                chief_complaint = st.text_area("Details", value=voice_text)
            else:
                chief_complaint = st.text_area("Details")
        else:
            chief_complaint = st.text_area("Details", height=80)

        st.markdown(f"### {T['ayush']}")
        c1, c2, c3 = st.columns(3)
        with c1: prakriti = st.selectbox(T["prakriti"], ["Unknown", "Vata", "Pitta", "Kapha", "Mixed"])
        with c2: agni = st.selectbox(T["agni"], ["Unknown", "Samagni", "Vishamagni", "Tikshnagni", "Mandagni"])
        with c3: koshtha = st.selectbox(T["koshtha"], ["Unknown", "Krura", "Madhya", "Mridu"])
        ayurveda_dict = {"prakriti": prakriti, "agni": agni, "koshtha": koshtha}
        
        st.subheader(f"📊 {T['vitals']}")
        c1, c2, c3, c4 = st.columns(4)
        with c1: bp_sys = st.number_input("BP Sys", 0, 300, 120)
        with c2: bp_dia = st.number_input("BP Dia", 0, 200, 80)
        with c3: pulse = st.number_input("Pulse", 0, 300, 72)
        with c4: temp = st.number_input("Temp °F", 0.0, 110.0, 98.6)
        
        if st.form_submit_button(T["register_btn"]):
            if not name or not chief_complaint or not username or not password: st.error("⚠️ Required fields missing!")
            elif db.get_patient_by_username(username): st.error("❌ Username exists!")
            else:
                p_data = {"name": name, "age": age, "gender": gender, "phone": phone, "email": email, "blood_group": blood_group, "conditions": "None", "allergies": "None", "chief_complaint": chief_complaint, "symptoms": "None", "bp": f"{bp_sys}/{bp_dia}", "pulse": pulse, "temperature": temp, "red_flags": [], "username": username, "password": security.hash_password(password), "ayurveda_data": json.dumps(ayurveda_dict)}
                db.save_patient(p_data)
                st.success(f"✅ Registered Successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: LOGINS
# ============================================================
elif page == "🔐 Patient Login":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    with st.form("p_login"):
        u = st.text_input(T["user"]); p = st.text_input(T["pass"], type="password")
        if st.form_submit_button(T["login_btn"]):
            pat = db.get_patient_by_username(u)
            if pat and security.verify_password(pat['password'], p):
                st.session_state.logged_in_patient = pat
                navigate_to("📤 Upload Report")
            else: st.error("❌ Invalid credentials")
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "👨‍⚕️ Doctor Login":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.info("Demo: `dr.sharma` / `doctor123`")
    with st.form("d_login"):
        u = st.text_input(T["user"]); p = st.text_input(T["pass"], type="password")
        if st.form_submit_button(T["login_btn"]):
            doc = db.get_doctor_by_username(u)
            if doc and security.verify_password(doc['password'], p):
                st.session_state.logged_in_doctor = doc
                navigate_to("🩺 Doctor Dashboard")
            else: st.error("❌ Invalid credentials")
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: UPLOAD REPORT
# ============================================================
elif page == "📤 Upload Report":
    pat = st.session_state.logged_in_patient
    if not pat: st.warning("⚠️ Login required")
    else:
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        up_file = st.file_uploader(T["upload_pdf"], type=["pdf"])
        if up_file:
            file_bytes = up_file.read()
            b64_pdf = base64.b64encode(file_bytes).decode('utf-8')
            with st.spinner(T["analyzing"]):
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                text = "".join([p.get_text() for p in doc])
                found_params = []
                for param, pattern in patterns.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        val = float(match.group(1))
                        r_info = reference_ranges.get(param, {})
                        st_val = "🔴 LOW" if val < r_info.get("min", 0) else ("🔴 HIGH" if val > r_info.get("max", 0) else "🟢 NORMAL")
                        found_params.append({"Parameter": param, "Value": val, "Unit": r_info.get("unit", "N/A"), "Status": st_val})
                
                if found_params:
                    st.dataframe(pd.DataFrame(found_params), use_container_width=True)
                    db.save_report(pat['patient_id'], up_file.name, found_params, file_data=b64_pdf)
                    st.success("Report Saved!")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: MY PRESCRIPTIONS
# ============================================================
elif page == "💊 My Prescriptions":
    if not st.session_state.logged_in_patient: st.warning("⚠️ Login required")
    else:
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        prescs = db.get_prescriptions_by_patient(st.session_state.logged_in_patient['patient_id'])
        if not prescs: st.info("No prescriptions yet.")
        else:
            for p in prescs:
                st.markdown(f'<div class="patient-info"><h3>💊 {p["diagnosis"]}</h3><p><b>Medicines:</b> {p["medicines"]}</p><p><b>Advice:</b> {p["advice"]}</p></div>', unsafe_allow_html=True)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=16, style='B')
                pdf.cell(200, 10, txt="MediScan Pro - e-Prescription", ln=True, align='C')
                pdf.set_font("Arial", size=12)
                pdf.ln(10)
                pdf.cell(200, 10, txt=f"Patient Name: {st.session_state.logged_in_patient['name']}", ln=True)
                pdf.cell(200, 10, txt=f"Diagnosis: {p['diagnosis']}", ln=True)
                pdf.cell(200, 10, txt=f"Medicines: {p['medicines']}", ln=True)
                pdf.cell(200, 10, txt=f"Advice: {p['advice']}", ln=True)
                pdf.ln(20)
                pdf.cell(200, 10, txt="Doctor's Signature: ___________________", ln=True, align='R')
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(label=T["download_pdf"], data=pdf_bytes, file_name=f"Prescription_{p['prescription_id']}.pdf", mime="application/pdf")
                st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: DOCTOR DASHBOARD
# ============================================================
elif page == "🩺 Doctor Dashboard":
    doc = st.session_state.logged_in_doctor
    if not doc: st.warning("⚠️ Login required")
    else:
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.subheader(f"🩺 Welcome {doc['name']}")
        appts = db.get_appointments_by_doctor(doc['doctor_id'])
        
        if not appts: st.info("📭 No appointments today.")
        else:
            for a in appts:
                with st.expander(f"🎫 Token {a['token_number']} — {a['patient_name']} — {a['status']}"):
                    p_data = db.get_patient(a['patient_id'])
                    
                    if p_data and p_data.get('red_flags'):
                        st.error(f"🚨 EMERGENCY ALERT: Red-flag symptoms detected! ({p_data['red_flags']})")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Complaint:** {a['chief_complaint']}")
                        
                        if p_data and p_data.get('ayurveda_data'):
                            ayur = json.loads(p_data['ayurveda_data'])
                            st.info(f"🕉️ **AYUSH:** Prakriti: {ayur.get('prakriti')} | Agni: {ayur.get('agni')} | Koshtha: {ayur.get('koshtha')}")
                            
                        st.markdown("### 📋 Completeness")
                        chk = completeness_engine.check_clinical_completeness(p_data)
                        for item, det in chk.items():
                            if det['status'] == "Completed": st.success(f"✅ {item}")
                            elif det['status'] == "Needs Verification": st.warning(f"⚠️ {item}")
                            else: st.error(f"❌ {item}")
                    
                    with c2:
                        reps = db.get_patient_reports(a['patient_id'])
                        if reps and reps[0].get('file_data'):
                            st.markdown(f"### {T['view_pdf']}")
                            pdf_display = f'<iframe src="data:application/pdf;base64,{reps[0]["file_data"]}" width="100%" height="400" style="border:none; border-radius:10px; background: white;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.info("No PDF Uploaded.")
                    
                    if a['status'] == 'In Consultation':
                        with st.form(f"notes_{a['appointment_id']}"):
                            st.markdown(f"#### {T['notes']}")
                            notes = st.text_area("Observations", value=a.get('doctor_notes', ''))
                            st.markdown(f"#### {T['presc']}")
                            diag = st.text_input(T["diagnosis"])
                            meds = st.text_area(T["meds"])
                            advice = st.text_input("Advice", value="Rest")
                            
                            if st.form_submit_button(T["save"]):
                                db.save_doctor_notes(a['appointment_id'], notes)
                                db.save_prescription(a['appointment_id'], a['patient_id'], doc['doctor_id'], diag, meds, advice, str(datetime.today()))
                                st.success("✅ Records Saved!")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGE: AI CHATBOT & ABOUT
# ============================================================
elif page == "💬 AI Chatbot":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    for c in st.session_state.chat:
        with st.chat_message("user"): st.write(c["q"])
        with st.chat_message("assistant"): st.write(c["a"])
    q = st.chat_input("Ask health questions...")
    if q:
        with st.chat_message("user"): st.write(q)
        with st.chat_message("assistant"):
            ans = ai_chat_response(q, None, st.session_state.logged_in_patient)
            st.write(ans)
        st.session_state.chat.append({"q": q, "a": ans})
    st.markdown('</div>', unsafe_allow_html=True)

elif page == "ℹ️ About":
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    st.subheader(f"{T['about']} MediScan Pro")
    st.markdown("**Version:** 8.0 (Multilingual + AYUSH + Voice + 3D UI)\n\n **Security:** PBKDF2 Hashing")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""<div class="footer"><p>🩺 MediScan Pro v8.0</p></div>""", unsafe_allow_html=True)