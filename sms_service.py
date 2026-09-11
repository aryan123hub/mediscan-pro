"""
SMS Service (Simulated)
Real SMS ke liye Twilio chahiye (paid) - yeh demo version hai
"""
from datetime import datetime
import database as db


def send_sms(patient_id, phone, message):
    """
    SMS bhejo (simulated) aur database mein log karo
    Real SMS ke liye Twilio integrate karna hoga
    """
    # Console mein print karo (demo ke liye)
    print("\n" + "=" * 60)
    print(f"📱 SMS SENT TO: {phone}")
    print("=" * 60)
    print(message)
    print("=" * 60 + "\n")
    
    # Database mein log karo
    db.log_sms(patient_id, phone, message)
    
    return True


def send_appointment_confirmation(patient_id, phone, patient_name, doctor_name, specialist, token, slot_time, date):
    """Appointment confirmation SMS"""
    message = f"""
Dear {patient_name},
Aapka appointment confirm ho gaya hai!

👨‍⚕️ Doctor: {doctor_name}
🏥 Specialist: {specialist}
🎫 Token Number: {token}
⏰ Time: {slot_time}
📅 Date: {date}

Kripya time se pehle pahunchein.
- MediScan Pro
    """.strip()
    
    return send_sms(patient_id, phone, message)


def send_token_update(patient_id, phone, patient_name, token, patients_ahead):
    """Token update SMS - jab patient ka number aane wala ho"""
    wait_time = patients_ahead * 10  # 10 min per patient
    
    message = f"""
Dear {patient_name},
Aapka token number {token} hai.

⏳ Aapse pehle {patients_ahead} patients hain.
⏰ Approximate wait time: {wait_time} minutes

Kripya waiting area mein rahein.
- MediScan Pro
    """.strip()
    
    return send_sms(patient_id, phone, message)


def send_prescription_ready(patient_id, phone, patient_name, doctor_name, diagnosis):
    """Prescription ready SMS"""
    message = f"""
Dear {patient_name},
Aapka prescription ready hai!

👨‍⚕️ Doctor: {doctor_name}
📋 Diagnosis: {diagnosis}

Aap patient portal se prescription dekh sakte hain.
- MediScan Pro
    """.strip()
    
    return send_sms(patient_id, phone, message)


def send_red_flag_alert(patient_id, phone, patient_name, red_flags):
    """Emergency red flag SMS"""
    flags_text = ", ".join(red_flags)
    message = f"""
🚨 EMERGENCY ALERT 🚨

Dear {patient_name},
Aapke symptoms mein emergency signs mile hain:
{flags_text}

Kripya turant medical help lein!

Emergency: 108
- MediScan Pro
    """.strip()
    
    return send_sms(patient_id, phone, message)


def send_followup_reminder(patient_id, phone, patient_name, follow_up_date):
    """Follow-up reminder SMS"""
    message = f"""
Dear {patient_name},
Aapka follow-up appointment {follow_up_date} ko hai.

Kripya time se aayein.
- MediScan Pro
    """.strip()
    
    return send_sms(patient_id, phone, message)


def get_patient_sms_history(patient_id):
    """Patient ke saare SMS history"""
    return db.get_sms_log(patient_id)


# ---------- TESTING ----------
if __name__ == "__main__":
    print("=" * 60)
    print("📱 SMS SERVICE - TESTING")
    print("=" * 60)
    
    # Test SMS send
    print("\n📋 Test 1: Appointment Confirmation")
    send_appointment_confirmation(
        patient_id=1,
        phone="9876543210",
        patient_name="Raj Kumar",
        doctor_name="Dr. Sharma",
        specialist="Cardiologist",
        token=15,
        slot_time="10:30 AM",
        date="10/09/2026"
    )
    
    print("\n📋 Test 2: Token Update")
    send_token_update(
        patient_id=1,
        phone="9876543210",
        patient_name="Raj Kumar",
        token=15,
        patients_ahead=3
    )
    
    print("\n📋 Test 3: Prescription Ready")
    send_prescription_ready(
        patient_id=1,
        phone="9876543210",
        patient_name="Raj Kumar",
        doctor_name="Dr. Sharma",
        diagnosis="Hypertension - Stage 1"
    )
    
    print("\n📋 Test 4: Red Flag Alert")
    send_red_flag_alert(
        patient_id=1,
        phone="9876543210",
        patient_name="Raj Kumar",
        red_flags=["chest pain", "breathing problem"]
    )
    
    print("\n" + "=" * 60)
    print("✅ ALL SMS TESTS COMPLETE!")
    print("=" * 60)