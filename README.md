# RxSafe

Polypharmacy risk intelligence for exploring medication burden in synthetic and uploaded test datasets.

**[Python 3.13 tested]** **[Streamlit]** **[Synthetic sample included]**

---

## The Problem

Medication histories can accumulate across prescribers and care settings, making review difficult. Older adults with complex medication regimens need careful assessment of potential harms and benefits. RxSafe explores a transparent way to prioritise records for review in a hackathon demonstration. It does not establish clinical risk or replace professional assessment.

## What RxSafe Does

- **Risk landscape:** interactive Plotly bubbles showing age, medication-record count, score, and risk tier.
- **NHS prescribing context:** requests atorvastatin spending data from OpenPrescribing; displays an unavailable message if retrieval fails. Live retrieval has returned HTTP 403 in the development environment.
- **Review table:** the top 10 high-scoring records with names, ages, counts, scores, tiers, and flagged medicines.
- **Transparent scoring:** deterministic rules implemented in `risk_scorer.py` and documented below. The current in-app sidebar summarises the scoring approach.
- **Visible limitations:** five expandable disclosures with severity badges.

The dataset workspace also accepts a CSV pair, validates its structure, recalculates results, provides SHA-256 input fingerprints, and exports calculated results as CSV.

## Run Locally

### 1. Clone

```bash
git clone https://github.com/Tallsomeson/rxsafe.git
cd rxsafe
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Prepare data

Use the included `data/patients.csv` and `data/medications.csv`. If absent, visit [Synthea downloads](https://synthea.mitre.org/downloads), download the 1K CSV sample, extract it, and place those two files in `data/`.

For your own test dataset, choose **Upload CSV pair** in the app:

| File | Required columns | Optional columns |
|---|---|---|
| Patients | `Id`, `BIRTHDATE` | `FIRST`, `LAST` |
| Medications | `PATIENT`, `DESCRIPTION` | Other columns are allowed |

Use unique, non-empty patient IDs and valid non-future birthdates. Each medication reference must match a patient ID. Only patients aged 65+ appear in the scored cohort. Upload synthetic or appropriately de-identified test data; uploaded provenance is the uploader's responsibility. Inputs are processed by the Streamlit server and are not sent to OpenPrescribing.

### 5. Run

```bash
python -m streamlit run app.py
```

The app opens at [localhost:8501](http://localhost:8501).

## Project Structure

```text
rxsafe/
├── data/
│   ├── patients.csv       # Synthetic patient records
│   └── medications.csv    # Synthetic medication histories
├── app.py                # Streamlit dashboard and upload workspace
├── data_loader.py        # CSV validation, loading and API request
├── risk_scorer.py        # Rule-based scoring
├── requirements.txt      # Pinned direct dependencies
└── README.md
```

## The Risk Scoring Formula

```python
total_score = min(
    medication_count * 10
    + max(0, (age - 65) * 0.5)
    + flagged_drug_points * 5,
    100,
)
```

`medication_count` counts all medication rows associated with a patient, including historical and repeated records. It does **not** measure distinct concurrent drugs. Age is approximated by elapsed days divided by 365. Each matching drug name contributes its points once, using case-insensitive substring matching across descriptions.

| Tier | Implemented threshold | Interpretation |
|---|---|---|
| High | 70–100 | Highest demonstration-score group |
| Moderate | 40 to below 70 | Intermediate demonstration-score group |
| Low | Below 40 | Lowest demonstration-score group |

These are unvalidated demonstration thresholds, not clinical recommendations or medication-review deadlines.

| Group | Drug names | Points before multiplication by 5 |
|---|---|---|
| Anticoagulants | warfarin, rivaroxaban, apixaban, edoxaban, dabigatran | 3 each |
| NSAIDs | ibuprofen, naproxen, diclofenac, celecoxib | 2 each |
| Diuretics | furosemide, spironolactone, bumetanide | 2 each |
| Opioids | morphine, oxycodone, fentanyl | 3 each |
| Opioids | tramadol, codeine | 2 each |
| Diabetes medicines | glibenclamide | 3 |
| Diabetes medicines | insulin, glipizide, gliclazide | 2 each |

The code comments refer to NHS polypharmacy guidance and STOPP/START as background. This formula is not a validated implementation of those clinical criteria.

## Data Sources

| Source | Provider | Licence recorded by project | Granularity | Used for |
|---|---|---|---|---|
| Synthea CSV sample | MITRE Corporation | Apache 2.0 | Synthetic patient-level records | Demographics and medication histories |
| OpenPrescribing API | Bennett Institute, University of Oxford | Open Government Licence v3.0 | Aggregate prescribing data | Population-level spending context |
| Uploaded CSVs | User | Determined by uploader | Patient-shaped test records | Independent pipeline testing |

> The bundled sample contains fictional patients. That assurance does not automatically apply to uploaded files. No patient records are transmitted to the prescribing API; its request contains a prescribing code.

## Known Limitations and Bias

These limitations appear in the app as severity-badged expandable cards:

1. **Demographic bias — HIGH:** the supplied sample is not established as representative of UK primary care.
2. **Social complexity — HIGH:** the formula does not model social circumstances, frailty, or access to care; performance in these groups has not been validated.
3. **Interaction completeness — MEDIUM:** the scorer searches 21 drug-name strings; it does not evaluate pairwise interactions or comprehensive contraindications.
4. **Clinical use — CRITICAL:** outputs are demonstration flags for human review, not diagnoses or prescribing advice.
5. **API granularity — LOW:** aggregate prescribing trends cannot establish an individual's risk.

Additional implementation limits include historical-row counting, approximate ages, no exclusion of deceased patients, and dependence on an external API that may block requests. A high score can reflect a long recorded history rather than a large active medication regimen.

## Architecture

`data_loader.py` reads and validates CSVs, derives display names and approximate ages, counts medication rows with Pandas, and selects the 65+ cohort. It separately requests aggregate spending data from OpenPrescribing. `risk_scorer.py` groups medication descriptions by patient and applies deterministic rules. `app.py` presents a light clinical dashboard, dataset uploads, charts, a review table, exports, and limitation expanders; the bundled data pipeline uses Streamlit caching.

## Stack

| Layer | Technology |
|---|---|
| Language | Python; tested locally on 3.13 |
| UI | Streamlit 1.39.0 |
| Visualisation | Plotly 5.24.1 |
| Processing | Pandas 2.2.3 |
| HTTP | Requests 2.32.3 |
| Synthetic sample | Synthea |
| External prescribing context | OpenPrescribing |

## What's Next

1. Define and validate a snapshot-based active-medication count before interpreting polypharmacy.
2. Investigate licensed pairwise interaction data and explicit STOPP/START rule mapping.
3. Evaluate UK-representative cohorts and subgroup performance.
4. Explore human-reviewed medication-review summaries after clinical validation.
5. Investigate practice-level summaries only where an appropriate practice mapping exists; do not infer patient links from aggregate API data.

## Responsible AI Statement

RxSafe uses deterministic rules rather than a machine-learning model. The scoring logic is inspectable, but transparency is not evidence of clinical validity. The application surfaces limitations where results are viewed. The bundled sample is synthetic, while uploaded data requires separate provenance and permission checks. Any real-world clinical use requires validation and appropriate governance.

## Licence

Application code: MIT Licence. A corresponding `LICENSE` file should accompany this declaration.

Data-source licences are separate:

- Synthea sample: Apache 2.0, as recorded by this project.
- OpenPrescribing data: Open Government Licence v3.0, as recorded by this project.
- Uploaded data: retain and respect the uploader's applicable terms.
