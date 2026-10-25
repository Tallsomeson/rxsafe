"""
RxSafe Polypharmacy Risk Scoring Engine

DESIGN PRINCIPLE: Full transparency. No black box.
This formula is published in the app UI and in this file.
Every clinician reviewing an output can verify every number.
"""

# High-risk drug classes with point values
# Based on STOPP/START criteria and NHS polypharmacy guidance
HIGH_RISK_DRUG_CLASSES = {
    # Anticoagulants — high bleed risk, narrow therapeutic index
    'warfarin': 3,
    'rivaroxaban': 3,
    'apixaban': 3,
    'edoxaban': 3,
    'dabigatran': 3,

    # NSAIDs — GI bleed risk, renal impairment in elderly
    'ibuprofen': 2,
    'naproxen': 2,
    'diclofenac': 2,
    'celecoxib': 2,

    # Diuretics — electrolyte disturbance, fall risk
    'furosemide': 2,
    'spironolactone': 2,
    'bumetanide': 2,

    # Opioids — fall risk, constipation, dependency
    'morphine': 3,
    'oxycodone': 3,
    'tramadol': 2,
    'codeine': 2,
    'fentanyl': 3,

    # Diabetes medications — hypoglycaemia risk
    'insulin': 2,
    'glipizide': 2,
    'gliclazide': 2,
    'glibenclamide': 3,  # highest hypoglycaemia risk in class
}


def get_patient_medications(patient_id, medications_df):
    """Return list of medication descriptions for one patient."""
    patient_meds = medications_df[
        medications_df['PATIENT'] == patient_id
    ]['DESCRIPTION'].str.lower().tolist()
    return patient_meds


def calculate_risk_score(patient_row, patient_meds):
    """
    Calculate polypharmacy risk score for one patient.

    FORMULA (published — not a black box):
      base_score  = medication_count × 10
      age_score   = max(0, (age - 65) × 0.5)
      drug_score  = sum of high-risk class points × 5
      total       = min(base + age + drug, 100)

    RISK TIERS:
      🔴 High Risk     = 70–100
      🟡 Moderate Risk = 40–69
      🟢 Low Risk      = 0–39

    Returns: (score: float, tier: str, flagged_drugs: list)
    """
    # Component 1: Medication count (primary driver)
    base_score = patient_row['med_count'] * 10

    # Component 2: Age penalty (risk increases with age)
    age_score = max(0, (patient_row['age'] - 65) * 0.5)

    # Component 3: High-risk drug class detection
    flagged_drugs = []
    drug_points = 0
    for drug_name, points in HIGH_RISK_DRUG_CLASSES.items():
        if any(drug_name in med for med in patient_meds):
            flagged_drugs.append(drug_name.title())
            drug_points += points
    drug_score = drug_points * 5

    # Total score — capped at 100
    total = min(100, base_score + age_score + drug_score)

    # Assign risk tier
    if total >= 70:
        tier = "🔴 High Risk"
    elif total >= 40:
        tier = "🟡 Moderate Risk"
    else:
        tier = "🟢 Low Risk"

    return round(total, 1), tier, flagged_drugs


def apply_risk_scores(patients_df, medications_df):
    """Apply risk scoring to entire patient DataFrame. Returns enriched DataFrame."""
    # Pre-process medications into a lookup dictionary for O(N) performance
    med_lookup = (
        medications_df.groupby('PATIENT')['DESCRIPTION']
        .apply(lambda x: [m.lower() for m in x.tolist()])
        .to_dict()
    )

    def process_row(row):
        patient_meds = med_lookup.get(row['Id'], [])
        return calculate_risk_score(row, patient_meds)

    results = patients_df.apply(process_row, axis=1)
    
    patients_df = patients_df.copy()
    patients_df['risk_score'] = results.apply(lambda x: x[0])
    patients_df['risk_tier'] = results.apply(lambda x: x[1])
    patients_df['flagged_drugs'] = results.apply(
        lambda x: ', '.join(x[2]) if x[2] else 'None flagged'
    )
    return patients_df
