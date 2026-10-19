import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os

# ============================================================
# 🔑 DATABASE CONNECTION STRING
# ============================================================
# YAHAN APNI SUPABASE CONNECTION STRING DAALO
# ============================================================
# 🔑 DATABASE CONNECTION
# ============================================================
# Streamlit Secrets se aayega (cloud pe)
# Ya environment variable se (local pe)
DB_URL = None

try:
    import streamlit as st
    DB_URL = st.secrets.get("DATABASE_URL", None)
except:
    pass

# Fallback: local testing ke liye
if not DB_URL:
    DB_URL = os.environ.get("DATABASE_URL", None)

# Agar abhi bhi nahi mila, toh error
if not DB_URL:
    print("⚠️ DATABASE_URL not found!")
    print("   Local: create .streamlit/secrets.toml")
    print("   Cloud: add secrets in Streamlit Cloud")
    DB_URL = "postgresql://postgres:aryan%4020069653@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

def get_connection():
    return psycopg2.connect(DB_URL)


def init_database():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database connection OK!")
    except Exception as e:
        print(f"❌ Connection error: {e}")


# ---------- PATIENT FUNCTIONS ----------
def save_patient(patient_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patients 
        (name, age, gender, phone, email, blood_group, conditions, allergies,
         chief_complaint, symptoms, bp, pulse, temperature, red_flags, username, password, ayurveda_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING patient_id
    """, (
        patient_data.get("name"), patient_data.get("age"),
        patient_data.get("gender"), patient_data.get("phone"),
        patient_data.get("email"), patient_data.get("blood_group"),
        patient_data.get("conditions"), patient_data.get("allergies"),
        patient_data.get("chief_complaint"), patient_data.get("symptoms"),
        patient_data.get("bp"), patient_data.get("pulse"),
        patient_data.get("temperature"),
        ", ".join(patient_data.get("red_flags", [])),
        patient_data.get("username"), patient_data.get("password"), patient_data.get("ayurveda_data")
    ))
    patient_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return patient_id


def get_patient_by_username(username):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM patients WHERE username = %s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def get_all_patients():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def get_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


# ---------- DOCTOR FUNCTIONS ----------
def save_doctor(doctor_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doctors 
        (name, specialist, qualification, phone, email, available_days, available_time, username, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING doctor_id
    """, (
        doctor_data.get("name"), doctor_data.get("specialist"),
        doctor_data.get("qualification"), doctor_data.get("phone"),
        doctor_data.get("email"), doctor_data.get("available_days"),
        doctor_data.get("available_time"), doctor_data.get("username"),
        doctor_data.get("password")
    ))
    doctor_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return doctor_id


def get_doctor_by_username(username):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM doctors WHERE username = %s", (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def get_all_doctors():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM doctors ORDER BY name")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def get_doctors_by_specialist(specialist):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM doctors WHERE specialist = %s AND status = 'Available'",
        (specialist,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def update_doctor_status(doctor_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE doctors SET status = %s WHERE doctor_id = %s", (status, doctor_id))
    conn.commit()
    cursor.close()
    conn.close()


# ---------- APPOINTMENT FUNCTIONS ----------
def create_appointment(patient_id, doctor_id, specialist, slot_time):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(*) FROM appointments 
        WHERE appointment_date = %s AND doctor_id = %s
    """, (today, doctor_id))
    count = cursor.fetchone()[0]
    token = count + 1
    
    cursor.execute("""
        INSERT INTO appointments 
        (patient_id, doctor_id, specialist, token_number, slot_time, appointment_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Waiting')
        RETURNING appointment_id
    """, (patient_id, doctor_id, specialist, token, slot_time, today))
    
    appointment_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return appointment_id, token


def get_appointments_by_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT a.*, d.name as doctor_name, d.specialist as doctor_specialist
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.patient_id = %s
        ORDER BY a.created_at DESC
    """, (patient_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def get_appointments_by_doctor(doctor_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT a.*, p.name as patient_name, p.age as patient_age, 
               p.gender as patient_gender, p.chief_complaint, p.symptoms
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id = %s AND a.appointment_date = %s
        ORDER BY a.token_number
    """, (doctor_id, today))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE appointments SET status = %s WHERE appointment_id = %s",
        (status, appointment_id)
    )
    conn.commit()
    cursor.close()
    conn.close()


# ---------- PRESCRIPTION FUNCTIONS ----------
def save_prescription(appointment_id, patient_id, doctor_id, diagnosis, medicines, advice, follow_up_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prescriptions 
        (appointment_id, patient_id, doctor_id, diagnosis, medicines, advice, follow_up_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING prescription_id
    """, (appointment_id, patient_id, doctor_id, diagnosis, medicines, advice, follow_up_date))
    prescription_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return prescription_id


def get_prescriptions_by_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT p.*, d.name as doctor_name 
        FROM prescriptions p
        JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE p.patient_id = %s
        ORDER BY p.created_at DESC
    """, (patient_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


# ---------- SMS FUNCTIONS ----------
def log_sms(patient_id, phone, message):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sms_log (patient_id, phone, message)
        VALUES (%s, %s, %s)
    """, (patient_id, phone, message))
    conn.commit()
    cursor.close()
    conn.close()


def get_sms_log(patient_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM sms_log WHERE patient_id = %s ORDER BY sent_at DESC",
        (patient_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]


# ---------- REPORT FUNCTIONS ----------
# database.py

def save_report(patient_id, filename, parameters, file_data=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (patient_id, filename, parameters, file_data)
        VALUES (%s, %s, %s, %s)
        RETURNING report_id
    """, (patient_id, filename, json.dumps(parameters), file_data))
    report_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return report_id

def get_patient_reports(patient_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM reports WHERE patient_id = %s ORDER BY uploaded_at DESC", (patient_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    reports = []
    for r in rows:
        d = dict(r)
        d['parameters'] = json.loads(d['parameters'])
        reports.append(d)
    return reports

def save_doctor_notes(appointment_id, notes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET doctor_notes = %s WHERE appointment_id = %s", (notes, appointment_id))
    conn.commit()
    cursor.close()
    conn.close()

# ---------- SEED DEFAULT DOCTORS ----------
def seed_default_doctors():
    doctors = [
        {"name": "Dr. Sharma", "specialist": "Cardiologist", "qualification": "MD, DM (Cardiology)", "phone": "9876543210", "email": "sharma@hospital.com", "available_days": "Mon-Sat", "available_time": "9AM-5PM", "username": "dr.sharma", "password": "doctor123"},
        {"name": "Dr. Verma", "specialist": "General Physician", "qualification": "MBBS, MD", "phone": "9876543211", "email": "verma@hospital.com", "available_days": "Mon-Sat", "available_time": "9AM-5PM", "username": "dr.verma", "password": "doctor123"},
        {"name": "Dr. Gupta", "specialist": "Neurologist", "qualification": "MD, DM (Neurology)", "phone": "9876543212", "email": "gupta@hospital.com", "available_days": "Mon-Fri", "available_time": "10AM-4PM", "username": "dr.gupta", "password": "doctor123"},
        {"name": "Dr. Singh", "specialist": "Pediatrician", "qualification": "MBBS, MD (Pediatrics)", "phone": "9876543213", "email": "singh@hospital.com", "available_days": "Mon-Sat", "available_time": "9AM-6PM", "username": "dr.singh", "password": "doctor123"},
        {"name": "Dr. Patel", "specialist": "Dermatologist", "qualification": "MBBS, MD (Dermatology)", "phone": "9876543214", "email": "patel@hospital.com", "available_days": "Mon-Fri", "available_time": "11AM-5PM", "username": "dr.patel", "password": "doctor123"},
        {"name": "Dr. Reddy", "specialist": "Orthopedic", "qualification": "MBBS, MS (Ortho)", "phone": "9876543215", "email": "reddy@hospital.com", "available_days": "Mon-Sat", "available_time": "10AM-6PM", "username": "dr.reddy", "password": "doctor123"},
        {"name": "Dr. Mehta", "specialist": "Gastroenterologist", "qualification": "MD, DM (Gastro)", "phone": "9876543216", "email": "mehta@hospital.com", "available_days": "Mon-Fri", "available_time": "9AM-3PM", "username": "dr.mehta", "password": "doctor123"},
        {"name": "Dr. Khan", "specialist": "Gynecologist", "qualification": "MBBS, MD (Gynae)", "phone": "9876543217", "email": "khan@hospital.com", "available_days": "Mon-Sat", "available_time": "9AM-5PM", "username": "dr.khan", "password": "doctor123"},
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for doc in doctors:
        cursor.execute("SELECT * FROM doctors WHERE username = %s", (doc["username"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO doctors 
                (name, specialist, qualification, phone, email, available_days, available_time, username, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (doc["name"], doc["specialist"], doc["qualification"],
                  doc["phone"], doc["email"], doc["available_days"],
                  doc["available_time"], doc["username"], doc["password"]))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Default doctors seeded!")


# Initialize
try:
    init_database()
    seed_default_doctors()
    print("✅ Database ready!")
except Exception as e:
    print(f"⚠️ Database error: {e}")