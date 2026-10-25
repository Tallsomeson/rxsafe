# RxSafe Main Application File
import streamlit as st
import plotly.express as px
import pandas as pd
from io import BytesIO
import hashlib
from data_loader import load_synthea_patients, get_openprescribing_data
from risk_scorer import apply_risk_scores

# ─── PAGE CONFIG ────────────────────────────────────
st.set_page_config(
    page_title="RxSafe — Polypharmacy Risk Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CUSTOM CSS ────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f8fbff 0%, #eef4fa 100%);
        color: #0B1222;
    }

    h1 { color: #0B1222; }
    .rx-summary-header {
        display: grid;
        grid-template-columns: 240px minmax(0, 1fr);
        gap: 20px;
        align-items: center;
        margin-bottom: 18px;
    }
    .rx-summary-header .rx-summary-banner { margin: 0; }
    .rx-summary-header .rx-section-title { font-size: 1.3rem; }
    .rx-panel { color: #0B1222; }
    [data-testid="stExpander"] { background: #ffffff; color: #0B1222; }
    .rx-metric-card { min-width: 0; }
    @media (min-width: 701px) and (max-width: 1100px) {
        .rx-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; }
    }
    @media (max-width: 700px) {
        .rx-summary-header { grid-template-columns: 1fr; }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    [data-testid="stExpander"] {
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
    }

    .main .block-container {
        max-width: 1320px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #1e3a5f;
    }

    h1, h2, h3, h4, p, li, span, div {
        color: inherit;
    }

    .rx-hero {
        display: grid;
        grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
        gap: 18px;
        align-items: start;
        margin-bottom: 18px;
    }

    .rx-brand {
        padding: 6px 4px 0 4px;
    }

    .rx-brand-mark {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 4px;
    }

    .rx-logo-pill {
        width: 22px;
        height: 22px;
        border-radius: 8px;
        background: linear-gradient(135deg, #6ba8ff 0%, #2563eb 100%);
        transform: rotate(45deg);
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
    }

    .rx-brand-name {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.05em;
        color: #102a5f;
    }

    .rx-brand-subtitle {
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.12;
        letter-spacing: -0.03em;
        color: #17346c;
        margin: 0.25rem 0;
    }

    .rx-brand-copy {
        margin: 0;
        max-width: 760px;
        color: #5f7394;
        font-size: 1rem;
        line-height: 1.65;
    }

    .rx-meta {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .rx-chip-row {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        flex-wrap: wrap;
    }

    .rx-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 14px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid transparent;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }

    .rx-chip-green {
        color: #0f7a46;
        background: rgba(34, 197, 94, 0.10);
        border-color: rgba(34, 197, 94, 0.20);
    }

    .rx-chip-blue {
        color: #1d4ed8;
        background: rgba(37, 99, 235, 0.10);
        border-color: rgba(37, 99, 235, 0.18);
    }

    .rx-chip-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
        display: inline-block;
    }

    .rx-panel,
    .data-provenance-banner {
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.08);
        backdrop-filter: blur(10px);
    }

    .rx-provenance-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        color: #17346c;
        margin-bottom: 10px;
        font-size: 0.95rem;
    }

    .rx-provenance-copy {
        margin: 0;
        color: #61748f;
        font-size: 0.80rem;
        line-height: 1.55;
    }

    .rx-provenance-copy strong {
        color: #17346c;
    }

    .rx-section-shell {
        margin-top: 16px;
        margin-bottom: 18px;
    }

    .rx-section-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: 12px;
    }

    .rx-section-title {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.05rem;
        font-weight: 800;
        color: #17346c;
        letter-spacing: -0.02em;
        margin-bottom: 3px;
    }

    .rx-section-icon {
        width: 26px;
        height: 26px;
        border-radius: 9px;
        background: rgba(37, 99, 235, 0.10);
        color: #2563eb;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        font-weight: 800;
        flex-shrink: 0;
    }

    .rx-section-caption {
        color: #6b7c96;
        font-size: 0.82rem;
        line-height: 1.55;
        margin: 0;
    }

    .rx-summary-banner {
        color: #5f7394;
        font-size: 0.95rem;
        line-height: 1.7;
        margin: 10px 0 16px 0;
    }

    .rx-summary-banner strong {
        color: #ef4444;
        font-weight: 800;
    }

    .rx-metric-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
    }

    .rx-metric-card,
    [data-testid="metric-container"] {
        border-radius: 16px;
        padding: 18px 16px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.5);
        min-height: 140px;
    }

    .rx-metric-blue {
        background: linear-gradient(180deg, #f4f9ff 0%, #edf5ff 100%);
    }

    .rx-metric-red {
        background: linear-gradient(180deg, #fff5f5 0%, #fff0f0 100%);
    }

    .rx-metric-orange {
        background: linear-gradient(180deg, #fff7ef 0%, #fff3ea 100%);
    }

    .rx-metric-cyan {
        background: linear-gradient(180deg, #f4fbff 0%, #edf8ff 100%);
    }

    .rx-metric-head {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }

    .rx-metric-icon {
        font-size: 1.3rem;
        line-height: 1;
    }

    .rx-metric-label {
        color: #17346c;
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.25;
    }

    .rx-metric-value {
        font-size: 2.3rem;
        line-height: 1;
        font-weight: 800;
        color: #102a5f;
        letter-spacing: -0.04em;
    }

    .rx-metric-red .rx-metric-value,
    .rx-metric-red .rx-metric-delta {
        color: #ef4444;
    }

    .rx-metric-orange .rx-metric-value,
    .rx-metric-orange .rx-metric-delta {
        color: #f97316;
    }

    .rx-metric-meta {
        margin-top: 10px;
    }

    .rx-metric-delta {
        font-size: 0.90rem;
        font-weight: 700;
    }

    .rx-metric-subtitle {
        color: #6b7c96;
        font-size: 0.78rem;
        line-height: 1.5;
    }

    .rx-legend-box {
        background: #ffffff;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
        min-width: 240px;
    }

    .rx-legend-item {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #6b7c96;
        font-size: 0.80rem;
        margin-bottom: 8px;
    }

    .rx-legend-item:last-child {
        margin-bottom: 0;
    }

    .rx-legend-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .rx-side-card {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
        height: 100%;
    }

    .rx-side-title {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #17346c;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 14px;
    }

    .rx-step {
        display: flex;
        gap: 12px;
        margin-bottom: 14px;
    }

    .rx-step:last-child {
        margin-bottom: 0;
    }

    .rx-step-num {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #e7f1ff;
        color: #2563eb;
        font-size: 0.85rem;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
    }

    .rx-step-title {
        color: #17346c;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .rx-step-copy,
    .rx-tier-copy {
        color: #61748f;
        font-size: 0.80rem;
        line-height: 1.55;
        margin: 0;
    }

    .rx-tier-list {
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid rgba(148, 163, 184, 0.18);
    }

    .rx-tier-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        font-size: 0.80rem;
        color: #61748f;
    }

    .rx-tier-item:last-child {
        margin-bottom: 0;
    }

    .rx-limitations-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
    }

    .rx-limit-card {
        background: rgba(255, 255, 255, 0.86);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
        padding: 16px 14px;
        min-height: 175px;
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.05);
    }

    .rx-limit-title {
        color: #17346c;
        font-size: 0.86rem;
        font-weight: 800;
        line-height: 1.35;
        margin: 8px 0 8px 0;
    }

    .rx-limit-copy {
        color: #61748f;
        font-size: 0.78rem;
        line-height: 1.55;
        margin: 0;
    }

    .rx-footer,
    .rxsafe-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        flex-wrap: wrap;
        margin-top: 22px;
        color: #61748f;
        font-size: 0.80rem;
    }

    .rx-footer strong,
    .rx-footer a,
    .rxsafe-footer strong,
    .rxsafe-footer a {
        color: #1d4ed8;
        font-weight: 700;
        text-decoration: none;
    }

    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.92) !important;
        border: 1px solid rgba(148, 163, 184, 0.22) !important;
        border-radius: 18px !important;
        overflow: hidden !important;
        box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
    }

    [data-testid="stDataFrameResizable"] {
        border-radius: 18px !important;
    }

    [data-testid="stAlert"] {
        border-radius: 16px !important;
        border-width: 1px !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(37, 99, 235, 0.18) !important;
        background: #ffffff !important;
        color: #1d4ed8 !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08) !important;
    }

    .stButton > button:hover {
        border-color: rgba(37, 99, 235, 0.30) !important;
        transform: translateY(-1px);
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: #6b7c96 !important;
    }

    hr {
        display: none;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    @media (max-width: 1100px) {
        .rx-hero,
        .rx-metric-grid,
        .rx-limitations-grid {
            grid-template-columns: 1fr;
        }

        .rx-chip-row {
            justify-content: flex-start;
        }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Cache data loading — only runs once per session."""
    patients_df, medications_df = load_synthea_patients(
        "data/patients.csv",
        "data/medications.csv"
    )
    patients_df = apply_risk_scores(patients_df, medications_df)
    return patients_df, medications_df


def metric_card_html(icon, label, value, subtitle, accent_class, delta=None):
    delta_html = (
        f'<div class="rx-metric-delta">{delta}</div>' if delta is not None else ""
    )
    return f"""
    <div class="rx-metric-card {accent_class}">
        <div class="rx-metric-head">
            <div class="rx-metric-icon">{icon}</div>
            <div class="rx-metric-label">{label}</div>
        </div>
        <div class="rx-metric-value">{value}</div>
        <div class="rx-metric-meta">
            {delta_html}
            <div class="rx-metric-subtitle">{subtitle}</div>
        </div>
    </div>
    """


def limitation_tile_html(icon, title, body):
    return f"""
    <div class="rx-limit-card">
        <div class="rx-section-icon">{icon}</div>
        <div class="rx-limit-title">{title}</div>
        <p class="rx-limit-copy">{body}</p>
    </div>
    """


def section_heading_html(icon, title, caption):
    return f"""
    <div class="rx-section-shell">
        <div class="rx-section-title">
            <span class="rx-section-icon">{icon}</span>
            <span>{title}</span>
        </div>
        <p class="rx-section-caption">{caption}</p>
    </div>
    """


st.subheader("Dataset workspace")
dataset_mode = st.radio("Choose a dataset", ["Bundled Synthea sample", "Upload CSV pair"], horizontal=True)
st.caption("Use synthetic or de-identified test data. CSVs are processed by this app; they are not sent to OpenPrescribing.")
if dataset_mode == "Upload CSV pair":
    st.caption("Patients: Id, BIRTHDATE (YYYY-MM-DD); optional FIRST, LAST. Medications: PATIENT, DESCRIPTION. PATIENT must match Id.")
    patient_upload = st.file_uploader("Patient CSV", type=['csv'], key="patients_upload")
    medication_upload = st.file_uploader("Medication CSV", type=['csv'], key="medications_upload")
    if patient_upload is None or medication_upload is None:
        st.info("Upload both CSV files to calculate results. The sample is not used as a fallback.")
        st.stop()
    patient_bytes, medication_bytes = patient_upload.getvalue(), medication_upload.getvalue()
else:
    patient_bytes = medication_bytes = None

try:
    if dataset_mode == "Upload CSV pair":
        patients, medications = load_synthea_patients(BytesIO(patient_bytes), BytesIO(medication_bytes))
        patients = apply_risk_scores(patients, medications)
    else:
        patients, medications = load_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError, UnicodeDecodeError) as exc:
    st.error(f"Dataset could not be loaded: {exc}")
    st.stop()
if patients.empty:
    st.info("This dataset has no eligible patients aged 65 or older. Upload a different dataset.")
    st.stop()
st.info(f"Active dataset: {dataset_mode}. {len(patients):,} patients aged 65+; {len(medications):,} medication records.")
st.caption("Medication counts include all rows in the supplied history, not distinct concurrent drugs. Scores are an unvalidated demonstration formula.")
if patient_bytes is not None:
    with st.expander("Verify uploaded file fingerprints"):
        st.text("Patients SHA-256: " + hashlib.sha256(patient_bytes).hexdigest())
        st.text("Medications SHA-256: " + hashlib.sha256(medication_bytes).hexdigest())
st.download_button("Download calculated results", patients[['Id', 'age', 'med_count', 'risk_score', 'risk_tier', 'flagged_drugs']].to_csv(index=False).encode('utf-8'), file_name="rxsafe_results.csv", mime="text/csv")

total = len(patients)
high_risk = patients[patients["risk_tier"] == "🔴 High Risk"].copy()
high_risk_count = len(high_risk)
polypharmacy_count = len(patients[patients["med_count"] >= 5])
avg_meds = patients["med_count"].mean()
high_risk_pct = (high_risk_count / total * 100) if total else 0
poly_pct = (polypharmacy_count / total * 100) if total else 0

header_html = """
<div class="rx-hero">
    <div class="rx-brand">
        <div class="rx-brand-mark">
            <span class="rx-logo-pill"></span>
            <span class="rx-brand-name">RxSafe</span>
        </div>
        <div class="rx-brand-subtitle">Polypharmacy Risk Intelligence for Elderly Patients</div>
        <p class="rx-brand-copy">
            Identify patients at risk from complex medication regimens using
            transparent, data-driven insights.
        </p>
    </div>
    <div class="rx-meta">
        <div class="rx-chip-row">
            <span class="rx-chip rx-chip-green">
                <span class="rx-chip-dot"></span>
                Synthetic Data Only
            </span>
            <span class="rx-chip rx-chip-blue">NHS Hackathon 2026</span>
        </div>
        <div class="rx-panel">
            <div class="rx-provenance-title">
                <span class="rx-section-icon" style="width:22px;height:22px;border-radius:7px;">i</span>
                Data provenance
            </div>
            <p class="rx-provenance-copy">
                Synthea™ synthetic patients - MITRE Corporation (Apache 2.0)
                <br>
                OpenPrescribing API - Bennett Institute, University of Oxford (Open Government Licence v3.0)
                <br>
                <strong>Zero real patient data is used in this application.</strong>
            </p>
        </div>
    </div>
</div>
"""
if dataset_mode == "Upload CSV pair":
    header_html = header_html.replace("Synthetic Data Only", "Uploaded Test Data").replace("Zero real patient data is used in this application.", "Patient results calculated from your uploaded CSV pair.")
st.markdown(header_html, unsafe_allow_html=True)

summary_html = f"""
<div class="rx-panel">
    <div class="rx-summary-header">
    <div class="rx-section-title">
        <span class="rx-section-icon">#</span>
        <span>Executive Summary</span>
    </div>
    <div class="rx-summary-banner">
        Analysis of <strong>{total:,}</strong> eligible patients shows a significant prevalence
        of polypharmacy, with <strong>{poly_pct:.1f}%</strong> of patients on five or more medications
        and <strong>{high_risk_pct:.1f}%</strong> classified as high risk.
    </div>
    </div>
    <div class="rx-metric-grid">
        {metric_card_html("👥", "Patients Analysed", f"{total:,}", "Active cohort size", "rx-metric-blue", "Cohort 65+")}
        {metric_card_html("⚠️", "High Risk Patients", f"{high_risk_count:,}", "Scoring 70-100", "rx-metric-red", f"{high_risk_pct:.1f}% of cohort")}
        {metric_card_html("💊", "Polypharmacy (5+)", f"{polypharmacy_count:,}", "Medication burden", "rx-metric-red", f"{poly_pct:.1f}% of cohort")}
        {metric_card_html("➕", "Avg Medications", f"{avg_meds:.1f}", "Per patient", "rx-metric-cyan", "Mean count")}
    </div>
</div>
"""
summary_html = "".join(line.strip() for line in summary_html.splitlines())
st.markdown(summary_html, unsafe_allow_html=True)

st.markdown(section_heading_html(
    "↗",
    "Risk Landscape",
    "Each bubble represents one patient record. Position = age x medications. Size = risk score. Colour = risk tier."
), unsafe_allow_html=True)

legend_html = """
<div class="rx-legend-box">
    <div class="rx-legend-item">
        <span class="rx-legend-dot" style="background:#ef5350;"></span>
        <span>High Risk (70-100)</span>
    </div>
    <div class="rx-legend-item">
        <span class="rx-legend-dot" style="background:#ff9800;"></span>
        <span>Moderate Risk (40-69)</span>
    </div>
    <div class="rx-legend-item">
        <span class="rx-legend-dot" style="background:#66bb6a;"></span>
        <span>Low Risk (0-39)</span>
    </div>
</div>
"""
legend_col, spacer_col = st.columns([1, 4])
with legend_col:
    st.markdown(legend_html, unsafe_allow_html=True)

chart_data = patients.sample(min(350, len(patients)), random_state=42).copy()
# display_name is now pre-calculated in data_loader.py

fig = px.scatter(
    chart_data,
    x="age",
    y="med_count",
    size="risk_score",
    color="risk_tier",
    color_discrete_map={
        "🔴 High Risk": "#ef5350",
        "🟡 Moderate Risk": "#ff9800",
        "🟢 Low Risk": "#66bb6a"
    },
    hover_name="display_name",
    hover_data={
        "risk_score": ":.1f",
        "flagged_drugs": True,
        "age": True,
        "med_count": True,
        "risk_tier": False
    },
    labels={
        "age": "Patient Age (years)",
        "med_count": "Number of Medications",
        "risk_score": "Risk Score",
        "flagged_drugs": "Flagged Drug Classes"
    },
    size_max=34,
    opacity=0.72,
    template="plotly_white"
)
fig.update_traces(
    marker=dict(line=dict(width=0.5, color="rgba(255,255,255,0.55)"))
)
fig.update_layout(
    height=500,
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=12, r=18, b=52, l=52),
    xaxis=dict(
        title=dict(text="Patient Age (years)", font=dict(color="#556987", size=12)),
        gridcolor="rgba(148,163,184,0.20)",
        zeroline=False,
        tickfont=dict(color="#556987", size=11),
        range=[64, patients["age"].max() + 2]
    ),
    yaxis=dict(
        title=dict(text="Number of Medications", font=dict(color="#556987", size=12)),
        gridcolor="rgba(148,163,184,0.20)",
        zeroline=False,
        tickfont=dict(color="#556987", size=11)
    ),
    hoverlabel=dict(
        bgcolor="#ffffff",
        bordercolor="rgba(239,68,68,0.18)",
        font=dict(color="#17346c", size=12, family="Inter")
    )
)
fig.add_annotation(
    x=0.98, y=0.98, xref="paper", yref="paper",
    xanchor="right", yanchor="top",
    text="⚠️ High-Risk Zone", showarrow=False,
    font=dict(color="#fca5a5", size=12, family="Inter"),
    bgcolor="rgba(11,18,34,0.85)", borderpad=6
)
fig.add_annotation(
    x=0.02, y=0.02, xref="paper", yref="paper",
    xanchor="left", yanchor="bottom",
    text="Low complexity", showarrow=False,
    font=dict(color="#6ee7b7", size=12, family="Inter"),
    bgcolor="rgba(11,18,34,0.85)", borderpad=6
)
st.plotly_chart(fig, use_container_width=True)

top_review = high_risk.sort_values("risk_score", ascending=False).head(10).copy()
table_col, score_col = st.columns([3.3, 1.2], gap="large")

with table_col:
    st.markdown(section_heading_html(
        "👥",
        "Patients Recommended for Medication Review",
        "Top 10 highest scoring records in the active dataset."
    ), unsafe_allow_html=True)

    if top_review.empty:
        st.info("No high-risk patients were found in this cohort sample.")
    else:
        display_df = top_review[
            ["display_name", "age", "med_count", "risk_score", "risk_tier", "flagged_drugs"]
        ].copy()
        display_df.columns = [
            "Patient Name",
            "Age",
            "Medications",
            "Risk Score",
            "Risk Tier",
            "Flagged Drug Classes"
        ]
        display_df["Age"] = display_df["Age"].astype(int).astype(str) + " yrs"
        display_df["Risk Score"] = display_df["Risk Score"].map(lambda x: f"{x:.1f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

with score_col:
    st.markdown("""
    <div class="rx-side-card">
        <div class="rx-side-title">
            <span class="rx-section-icon">#</span>
            <span>How the Risk Score Works</span>
        </div>
        <div class="rx-step">
            <div class="rx-step-num">1</div>
            <div>
                <div class="rx-step-title">Patient factors</div>
                <p class="rx-step-copy">Age and total number of medications are key drivers of risk.</p>
            </div>
        </div>
        <div class="rx-step">
            <div class="rx-step-num">2</div>
            <div>
                <div class="rx-step-title">Medication risk</div>
                <p class="rx-step-copy">Higher risk is assigned to medicines commonly associated with adverse events in older adults.</p>
            </div>
        </div>
        <div class="rx-step">
            <div class="rx-step-num">3</div>
            <div>
                <div class="rx-step-title">Risk score (0-100)</div>
                <p class="rx-step-copy">Medication count, age, and flagged high-risk classes combine into a single transparent score.</p>
            </div>
        </div>
        <div class="rx-step">
            <div class="rx-step-num">4</div>
            <div>
                <div class="rx-step-title">Risk tiers</div>
                <p class="rx-step-copy">Scores support triage for review. They do not replace clinical judgement.</p>
            </div>
        </div>
        <div class="rx-tier-list">
            <div class="rx-tier-item"><span class="rx-legend-dot" style="background:#ef5350;"></span> High Risk: 70-100</div>
            <div class="rx-tier-item"><span class="rx-legend-dot" style="background:#ff9800;"></span> Moderate Risk: 40-69</div>
            <div class="rx-tier-item"><span class="rx-legend-dot" style="background:#66bb6a;"></span> Low Risk: 0-39</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(section_heading_html(
    "!",
    "Known Limitations and Bias Considerations",
    "We place limitations inside the interface itself so that caveats are visible at the point of use."
), unsafe_allow_html=True)

st.markdown("""
<div class="rx-panel" style="background: #fffbeb; border: 1px solid #f59e0b; border-left: 4px solid #f59e0b; color: #78350f; margin-bottom: 16px;">
    <strong>Caveats at the point of use</strong><br>
    Review these limitations before interpreting scores. Clinical users must encounter caveats at the point of use.
</div>
""", unsafe_allow_html=True)

limitations = [
    {'icon': '🌍', 'title': '1. Demographic bias in source data', 'severity': 'HIGH', 'color': '#ef4444', 'body': 'Synthea does not fully represent UK NHS demographics, so production thresholds would require UK-specific recalibration.'},
    {'icon': '🏘️', 'title': '2. Reduced validity for socially complex patients', 'severity': 'HIGH', 'color': '#f97316', 'body': 'Medication-count tools can understate risk for patients affected by frailty, housing instability, language barriers, or other social complexity.'},
    {'icon': '💊', 'title': '3. Drug interaction completeness', 'severity': 'MEDIUM', 'color': '#f59e0b', 'body': 'This version uses a simplified high-risk drug list rather than a full BNF interaction engine, so some interactions are not surfaced.'},
    {'icon': '⚠️', 'title': '4. Not a clinical decision tool', 'severity': 'CRITICAL', 'color': '#dc2626', 'body': 'RxSafe is designed to flag patients for human review only. No prescribing action should follow from the score alone.'},
    {'icon': '📊', 'title': '5. OpenPrescribing data granularity', 'severity': 'LOW', 'color': '#22c55e', 'body': 'The live NHS feed is practice-level aggregate data. It adds population context, but it cannot support patient-level inference.'},
]

for limitation in limitations:
    with st.expander(f"{limitation['icon']} {limitation['title']}"):
        st.markdown(
            f"<span style='display: inline-block; padding: 4px 10px; border-radius: 6px; "
            f"background: {limitation['color']}18; color: {limitation['color']}; "
            f"border: 1px solid {limitation['color']}; font-weight: 700; font-size: 0.8rem;'>"
            f"{limitation['severity']}</span>",
            unsafe_allow_html=True
        )
        st.markdown(limitation['body'])

st.markdown(section_heading_html(
    "↻",
    "Live NHS Prescribing Context",
    "Population-level prescribing trends from OpenPrescribing add real-world context without introducing identifiable patient data."
), unsafe_allow_html=True)
refresh_clicked = st.button("Refresh NHS data", help="Re-fetch OpenPrescribing data")

if refresh_clicked:
    st.cache_data.clear()

with st.spinner("Connecting to OpenPrescribing API..."):
    op_data = get_openprescribing_data()

if not op_data.empty and "actual_cost" in op_data.columns:
    op_data["date"] = pd.to_datetime(op_data["date"])
    recent = op_data.tail(24).copy()
    fig2 = px.area(
        recent,
        x="date",
        y="actual_cost",
        template="plotly_white",
        color_discrete_sequence=["#818cf8"],
        labels={"actual_cost": "Monthly Cost (£)", "date": "Month"}
    )
    fig2.update_traces(
        fillcolor="rgba(129,140,248,0.08)",
        line=dict(color="#818cf8", width=2)
    )
    fig2.update_layout(
        height=280,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=12, r=16, b=36, l=64),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.20)",
            tickfont=dict(color="#556987", size=11),
            zeroline=False
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.20)",
            tickfont=dict(color="#556987", size=11),
            tickprefix="£",
            zeroline=False
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="rgba(124,140,255,0.18)",
            font=dict(color="#17346c", size=12)
        )
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning(
        "OpenPrescribing API is currently unavailable. RxSafe still functions fully using synthetic patient data."
    )

st.markdown("""
<div class="rx-footer">
    <span><strong>RxSafe</strong> | Built for NHS Hackathon 2026</span>
    <span>Synthea data: Apache 2.0 | OpenPrescribing: OGL v3.0</span>
    <span><a href="https://github.com/Tallsomeson/rxsafe" target="_blank">GitHub Repository</a></span>
</div>
""", unsafe_allow_html=True)
