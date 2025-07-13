import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ========== HARD CODED CONFIGURATION ==========
SERVICE_ACCOUNT_JSON = {
    # Paste your service account JSON here as a Python dict!
    # Example:
    # "type": "service_account",
    # "project_id": "...",
    # ...
}
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"

tabs_columns = {
    "Basic Info": [
        "first_name","last_name","full_name","email","phone","company_id",
        "industry","position","company_size","website","source","assessment_date"
    ],
    "Contact Info": [
        "full_name","address_line_1","city","state","postal_code","country"
    ],
    "DISC General Profile": ["full_name","discprofile"],
    "DISC Sales Profile": ["full_name","discsales"],
    "DISC Communication Style": ["full_name","disc_communiction"],
    "DISC Leadership Style": ["full_name","leadership_style"],
    "DISC Team Dynamics": ["full_name","team_dynamics"],
    "DISC Conflict Resolution": ["full_name","conflict_resolution"],
    "DISC Customer Service Approach": ["full_name","customer_service_approach"],
    "DISC Decision-Making Style": ["full_name","decision_making_style"],
    "DISC Workplace Behavior": ["full_name","workplace_behavior"],
    "HR & Coaching": [
        "full_name","hiring_and_recruitment","_coaching_and_development",
        "career_goals","stress_management","learning_style"
    ],
}

st.set_page_config(page_title="CRM Full Manager", layout="wide", page_icon="📋")
st.markdown("<h1 style='font-size:3em;color:#4CAF50;'>📋 CRM Client Profiles Manager</h1>", unsafe_allow_html=True)

selected_tab = st.selectbox("Select CRM Section (Tab):", list(tabs_columns.keys()))
expected_columns = tabs_columns[selected_tab]

# ========== LOAD DATA ==========
@st.cache_data(show_spinner=False)
def load_gsheet_data():
    try:
        creds = Credentials.from_service_account_info(
            SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        try:
            worksheet = sh.worksheet(selected_tab)
            data = worksheet.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
            else:
                df = pd.DataFrame(columns=expected_columns)
        except gspread.exceptions.WorksheetNotFound:
            df = pd.DataFrame(columns=expected_columns)
        # Ensure all expected columns are present
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_columns]
        return df
    except Exception as e:
        st.error(f"❌ Could not load Google Sheet: {e}")
        return pd.DataFrame(columns=expected_columns)

df = load_gsheet_data()

# ========== CSV UPLOAD ==========
uploaded_file = st.file_uploader(f"Upload {selected_tab} CSV to append:", type=["csv"])
if uploaded_file:
    try:
        new_df = pd.read_csv(uploaded_file)
        for col in expected_columns:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[expected_columns]
        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()
        st.success("✅ CSV uploaded and merged!")
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")

# ========== VIEW & SELECT ==========
st.markdown("### 👀 Current Data")
st.dataframe(df, use_container_width=True, height=500)

if not df.empty:
    selected_idx = st.selectbox("Select a row to edit/delete:", df.index, format_func=lambda x: f"{df.at[x, expected_columns[0]]} | {df.at[x, expected_columns[1]] if len(expected_columns)>1 else ''}")
else:
    selected_idx = None

# ========== EDIT ==========
st.markdown("### ✏️ Edit Selected Row")
if selected_idx is not None and not df.empty:
    edit_data = {}
    cols = st.columns(len(expected_columns))
    for idx, col in enumerate(expected_columns):
        value = df.at[selected_idx, col]
        if col == "assessment_date":
            edit_data[col] = cols[idx].date_input(col, value=pd.to_datetime(value) if value else datetime.date.today())
        else:
            edit_data[col] = cols[idx].text_input(col, value=value)
    if st.button("💾 Save Edit"):
        for col in expected_columns:
            df.at[selected_idx, col] = edit_data[col]
        st.success("Row updated! (Don't forget to sync with Google Sheets below)")

    if st.button("🗑️ Delete Row"):
        df = df.drop(index=selected_idx).reset_index(drop=True)
        st.warning("Row deleted! (Don't forget to sync with Google Sheets below)")

# ========== ADD ==========
st.markdown("### ➕ Add New Entry")
with st.form("add_entry_form"):
    new_data = {}
    cols = st.columns(len(expected_columns))
    for idx, col in enumerate(expected_columns):
        if col == "assessment_date":
            new_data[col] = cols[idx].date_input(col, value=datetime.date.today())
        else:
            new_data[col] = cols[idx].text_input(col, placeholder=f"Enter {col}")
    submitted = st.form_submit_button("Add Entry")
    if submitted:
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        st.success("✅ New entry added! (Don't forget to sync with Google Sheets below)")

# ========== DOWNLOAD ==========
csv_data = df.to_csv(index=False)
st.download_button(
    label=f"📥 Download {selected_tab} CSV",
    data=csv_data,
    file_name=f"{selected_tab.lower().replace(' ','_')}.csv",
    mime='text/csv'
)

# ========== APPEND/UPDATE TO GOOGLE SHEETS ==========
def sync_to_gsheet(df):
    try:
        creds = Credentials.from_service_account_info(
            SERVICE_ACCOUNT_JSON,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        try:
            worksheet = sh.worksheet(selected_tab)
            sh.del_worksheet(worksheet)
            worksheet = sh.add_worksheet(title=selected_tab, rows="1000", cols="50")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=selected_tab, rows="1000", cols="50")
        worksheet.update([expected_columns] + df.fillna("").astype(str).values.tolist())
        st.success(f"✅ Google Sheet '{selected_tab}' updated!")
        st.info(f"[Open your Google Sheet](https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit)")
    except Exception as e:
        st.error(f"❌ Google Sheets error: {e}")

if st.button("🚀 Sync ALL Changes to Google Sheets (Overwrite Tab)"):
    sync_to_gsheet(df)

st.caption("✅ View, add, edit, select, and sync your CRM data. Built with ❤️ using Streamlit + Google Sheets.")
