def check_clinical_completeness(patient_data):
    """
    Patient ke data ko check karta hai aur batata hai ki kya kya missing hai.
    """
    checklist = {
        "Chief Complaint": {"status": "Missing", "reason": "Patient ki main problem nahi likhi gayi."},
        "Symptoms": {"status": "Missing", "reason": "Koi symptoms select nahi kiye gaye."},
        "Vital Signs (BP/Pulse/Temp)": {"status": "Missing", "reason": "Vitals nahi bhare gaye hain."},
        "Known Conditions": {"status": "Missing", "reason": "Medical history nahi hai."},
        "Allergies": {"status": "Missing", "reason": "Allergies ka pata nahi hai (Risk!)."}
    }

    # Chief Complaint Check
    if patient_data.get("chief_complaint") and patient_data.get("chief_complaint").strip() != "":
        checklist["Chief Complaint"] = {"status": "Completed", "reason": "Chief complaint recorded."}
    
    # Symptoms Check
    if patient_data.get("symptoms") and patient_data.get("symptoms") != "None":
        checklist["Symptoms"] = {"status": "Completed", "reason": "Symptoms recorded."}
    
    # Vitals Check
    if patient_data.get("bp") and patient_data.get("pulse") and patient_data.get("temperature"):
        checklist["Vital Signs (BP/Pulse/Temp)"] = {"status": "Completed", "reason": "All vitals recorded."}
    
    # Conditions Check
    if patient_data.get("conditions"):
        if patient_data.get("conditions") == "None":
            checklist["Known Conditions"] = {"status": "Needs Verification", "reason": "Marked as 'None'. Doctor should confirm."}
        else:
            checklist["Known Conditions"] = {"status": "Completed", "reason": "Conditions recorded."}
    
    # Allergies Check
    if patient_data.get("allergies"):
        if patient_data.get("allergies") == "None":
            checklist["Allergies"] = {"status": "Needs Verification", "reason": "Marked as 'None'. Confirm with patient."}
        else:
            checklist["Allergies"] = {"status": "Completed", "reason": "Allergies recorded."}

    return checklist