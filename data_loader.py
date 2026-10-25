import pandas as pd
import requests

def load_synthea_patients(patients_path, medications_path):
    """
    Load pre-generated Synthea synthetic patient data.
    
    DATA PROVENANCE:
    Source: synthea.mitre.org — MITRE Corporation
    Licence: Apache 2.0 — free for any use, no patient identifiability
    These are not real patients. No consent is required or applicable.
    Demographic note: Default Synthea data reflects US Massachusetts
    census demographics, not UK NHS demographics. Flagged as limitation.
    """
    patients = pd.read_csv(patients_path, low_memory=False, dtype={"Id": str})
    medications = pd.read_csv(medications_path, low_memory=False, dtype={"PATIENT": str, "DESCRIPTION": str})

    for label, frame, required in [
        ("Patients", patients, {"Id", "BIRTHDATE"}),
        ("Medications", medications, {"PATIENT", "DESCRIPTION"}),
    ]:
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{label} CSV missing columns: {', '.join(sorted(missing))}")
    if patients.empty or patients['Id'].isna().any() or patients['Id'].duplicated().any():
        raise ValueError("Patients must have unique, non-empty Id values and at least one row.")
    if medications['PATIENT'].isna().any() or not medications['PATIENT'].isin(patients['Id']).all():
        raise ValueError("Every medication PATIENT must match an Id in the patient CSV.")
    if medications['DESCRIPTION'].isna().any():
        raise ValueError("Medication DESCRIPTION values cannot be empty.")
    birthdates = pd.to_datetime(patients['BIRTHDATE'], errors='coerce')
    if birthdates.isna().any() or (birthdates > pd.Timestamp.now()).any():
        raise ValueError("BIRTHDATE must contain valid, non-future dates (YYYY-MM-DD).")
    for column in ('FIRST', 'LAST'):
        if column not in patients:
            patients[column] = 'Patient' if column == 'FIRST' else patients['Id']
        patients[column] = patients[column].fillna('').astype(str)

    # Calculate age from BIRTHDATE
    patients['BIRTHDATE'] = pd.to_datetime(
        patients['BIRTHDATE'], errors='coerce'
    )
    patients['age'] = (
        pd.Timestamp.now() - patients['BIRTHDATE']
    ).dt.days // 365

    # Count medications per patient
    med_counts = (
        medications.groupby('PATIENT')
        .size()
        .reset_index(name='med_count')
    )

    # Centralized Name Generation
    patients['display_name'] = (
        patients['FIRST'].fillna('Patient') + ' ' + 
        patients['LAST'].fillna('')
    ).str.strip()

    # Merge medication counts onto patients
    patients = patients.merge(
        med_counts,
        left_on='Id',
        right_on='PATIENT',
        how='left'
    )
    patients['med_count'] = patients['med_count'].fillna(0).astype(int)

    # Filter to 65+ cohort — our target population
    elderly = patients[patients['age'] >= 65].copy()
    return elderly, medications


def get_openprescribing_data(bnf_code='0212000B0'):
    """
    Fetch live NHS statin prescribing data from OpenPrescribing API.
    
    DATA PROVENANCE:
    Source: openprescribing.net — Bennett Institute for Applied Data Science
    Licence: Open Government Licence v3.0
    Granularity: PRACTICE LEVEL ONLY — aggregate counts, not patient records.
    No patient is identifiable at any point in this pipeline.
    BNF code 0212000B0 = Atorvastatin (most commonly prescribed statin in NHS)
    """
    url = (
        f"https://openprescribing.net/api/1.0/spending/"
        f"?code={bnf_code}&format=json"
    )
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        # Return empty DataFrame with expected columns if API is unavailable
        return pd.DataFrame(columns=['date', 'actual_cost', 'items'])
