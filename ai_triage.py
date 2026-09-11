"""
AI Triage System
Symptoms dekh kar specialist doctor assign karta hai
"""

import re

# ---------- SYMPTOM → SPECIALIST MAPPING ----------
# Har specialist ke liye keywords
SPECIALIST_KEYWORDS = {
    "Cardiologist": [
        "chest pain", "seene mein dard", "heart", "dil", "dhadkan",
        "palpitations", "bp", "blood pressure", "hypertension",
        "heart attack", "cardiac", "cholesterol", "shortness of breath",
        "saans", "breathing problem"
    ],
    "Neurologist": [
        "headache", "sar dard", "migraine", "seizure", "mirgi",
        "dizziness", "chakkar", "paralysis", "stroke", "numbness",
        "tingling", "memory loss", "bhoolna", "tremor", "kampa",
        "unconscious", "behosh"
    ],
    "General Physician": [
        "fever", "bukhar", "cough", "khansi", "cold", "jukam",
        "body ache", "badan dard", "weakness", "kamzori",
        "fatigue", "thakan", "vomiting", "ulti", "loose motion",
        "dast", "diarrhea", "infection", "sneezing", "chheenk"
    ],
    "Dermatologist": [
        "skin", "twacha", "rash", "daane", "itching", "khujli",
        "acne", "pimples", "muhase", "hair fall", "baal jhadna",
        "eczema", "psoriasis", "allergy", "daag", "warts"
    ],
    "Orthopedic": [
        "bone", "haddi", "joint pain", "jod mein dard", "knee pain",
        "ghutne", "back pain", "kamar dard", "fracture", "fracture",
        "sprain", "moch", "arthritis", "gathiya", "shoulder pain",
        "neck pain", "gardan dard"
    ],
    "Gastroenterologist": [
        "stomach", "pet", "abdominal pain", "pet dard", "acidity",
        "gas", "constipation", "kabz", "indigestion", "badhazmi",
        "liver", "liver", "ulcer", "nausea", "pet kharab",
        "blood in stool", "khoon"
    ],
    "Pediatrician": [
        "child", "bachcha", "baby", "infant", "shishu",
        "kid", "newborn", "vaccination", "teeka"
    ],
    "Gynecologist": [
        "pregnancy", "pregnant", "garbhvati", "periods", "menses",
        "menstrual", "mahavari", "gynec", "women", "female",
        "delivery", "prasav"
    ],
    "Psychiatrist": [
        "depression", "anxiety", "tension", "stress", "mental",
        "suicide", "mood", "sleep problem", "neend", "behaviour",
        "addiction", "nasha"
    ],
    "ENT Specialist": [
        "ear", "kaan", "nose", "naak", "throat", "gala",
        "tonsils", "sinus", "hearing", "sunai", "sore throat"
    ],
    "Ophthalmologist": [
        "eye", "aankh", "vision", "drishti", "blurred", "dhundhla",
        "redness", "laal", "itching in eyes", "chashma", "glasses"
    ]
}

# ---------- SYMPTOM SEVERITY (Red Flags) ----------
RED_FLAG_KEYWORDS = [
    "chest pain", "heart attack", "seene mein dard",
    "saans", "breathing problem", "unconscious", "behosh",
    "severe bleeding", "khoon", "paralysis", "stroke",
    "seizure", "mirgi", "suicide", "poison", "overdose",
    "fracture", "burns", "jal gaya", "accident"
]


def get_specialist(symptoms_text, age=30, gender="Male"):
    """
    Symptoms analyze karke specialist suggest karo
    Returns: (specialist, confidence, matched_keywords)
    """
    
    if not symptoms_text:
        return "General Physician", 0, []
    
    symptoms_lower = symptoms_text.lower()
    
    # Age-based override (Child)
    if age < 12:
        return "Pediatrician", 100, ["Age < 12"]
    
    # Gender-based override (Pregnancy)
    if gender.lower() == "female":
        if any(k in symptoms_lower for k in ["pregnancy", "pregnant", "garbhvati", "periods", "menses"]):
            return "Gynecologist", 100, ["Female + Pregnancy/Menstrual"]
    
    # Score each specialist
    scores = {}
    matched = {}
    
    for specialist, keywords in SPECIALIST_KEYWORDS.items():
        score = 0
        matched_kw = []
        for kw in keywords:
            if kw in symptoms_lower:
                score += 1
                matched_kw.append(kw)
        if score > 0:
            scores[specialist] = score
            matched[specialist] = matched_kw
    
    # Agar koi match nahi mila
    if not scores:
        return "General Physician", 0, []
    
    # Highest score wala specialist
    best_specialist = max(scores, key=scores.get)
    best_score = scores[best_specialist]
    
    # Confidence calculate karo (percentage)
    total_keywords = len(SPECIALIST_KEYWORDS[best_specialist])
    confidence = min(100, int((best_score / total_keywords) * 100) + 30)
    
    return best_specialist, confidence, matched[best_specialist]


def check_red_flags(symptoms_text, chief_complaint=""):
    """
    Emergency symptoms check karo
    Returns: list of red flags found
    """
    full_text = (symptoms_text + " " + chief_complaint).lower()
    found = [flag for flag in RED_FLAG_KEYWORDS if flag in full_text]
    return list(set(found))


def get_urgency_level(red_flags):
    """
    Red flags ke hisaab se urgency level
    """
    if red_flags:
        return "🚨 EMERGENCY", "Immediate attention required!"
    return "🟢 NORMAL", "Regular appointment"


def estimate_wait_time(token_number, avg_time_per_patient=10):
    """
    Token number se estimated wait time calculate karo
    """
    wait_minutes = (token_number - 1) * avg_time_per_patient
    if wait_minutes < 60:
        return f"{wait_minutes} minutes"
    else:
        hours = wait_minutes // 60
        mins = wait_minutes % 60
        return f"{hours} hours {mins} minutes"


def triage_patient(symptoms_text, age=30, gender="Male", chief_complaint=""):
    """
    Complete triage analysis
    Returns: dict with all info
    """
    specialist, confidence, matched_kw = get_specialist(symptoms_text, age, gender)
    red_flags = check_red_flags(symptoms_text, chief_complaint)
    urgency, urgency_msg = get_urgency_level(red_flags)
    
    return {
        "specialist": specialist,
        "confidence": confidence,
        "matched_keywords": matched_kw,
        "red_flags": red_flags,
        "urgency": urgency,
        "urgency_message": urgency_msg
    }


# ---------- TESTING ----------
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI TRIAGE SYSTEM - TESTING")
    print("=" * 60)
    
    # Test 1: Chest Pain
    print("\n📋 Test 1: Chest Pain")
    result = triage_patient("chest pain and shortness of breath", 45, "Male", "Chest pain")
    print(f"   Specialist: {result['specialist']}")
    print(f"   Confidence: {result['confidence']}%")
    print(f"   Urgency: {result['urgency']}")
    print(f"   Red Flags: {result['red_flags']}")
    
    # Test 2: Fever
    print("\n📋 Test 2: Fever")
    result = triage_patient("fever and cough since 3 days", 30, "Male", "Fever")
    print(f"   Specialist: {result['specialist']}")
    print(f"   Confidence: {result['confidence']}%")
    
    # Test 3: Child
    print("\n📋 Test 3: Child Patient")
    result = triage_patient("fever and cold", 5, "Male", "Fever")
    print(f"   Specialist: {result['specialist']}")
    
    # Test 4: Skin Problem
    print("\n📋 Test 4: Skin Problem")
    result = triage_patient("itching and rash on skin", 25, "Female", "Skin rash")
    print(f"   Specialist: {result['specialist']}")
    
    # Test 5: Headache
    print("\n📋 Test 5: Headache")
    result = triage_patient("severe headache and dizziness", 35, "Male", "Headache")
    print(f"   Specialist: {result['specialist']}")
    
    # Test 6: Pregnancy
    print("\n📋 Test 6: Pregnant Woman")
    result = triage_patient("pregnancy checkup", 28, "Female", "Pregnancy")
    print(f"   Specialist: {result['specialist']}")
    
    # Test 7: Wait Time
    print("\n⏰ Test 7: Wait Time Calculation")
    print(f"   Token 1: {estimate_wait_time(1)}")
    print(f"   Token 5: {estimate_wait_time(5)}")
    print(f"   Token 15: {estimate_wait_time(15)}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)