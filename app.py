import streamlit as st
import pandas as pd
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials

# =======================
# ✅ Set Streamlit Page Theme
# =======================
st.set_page_config(
    page_title="CRM Client Profiles Manager",
    layout="wide",
    page_icon="📋"
)

# =======================
# 🎨 Custom Styling Section
# =======================
st.markdown(
    """
    <style>
    .big-title {
        font-size: 3em;
        font-weight: bold;
        color: #4CAF50;
    }
    .section-header {
        font-size: 1.5em;
        margin-top: 2rem;
        color: #0066CC;
    }
    .info-text {
        color: #444;
        font-size: 1em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<div class='big-title'>📋 CRM Client Profiles Manager</div>", unsafe_allow_html=True)

st.markdown(
    """
    This app helps you manage your CRM client profiles in **separate tabs**!  
    ✅ Upload, edit, and download CSVs  
    ✅ Append new data to **Google Sheets tabs**  
    ✅ Share one Sheet with your whole team

    ---
    """
)

# ========================
# ⚙️ SIDEBAR CONFIGURATION
# ========================
st.sidebar.header("🔧 App Configuration")

theme_choice = st.sidebar.radio(
    "Choose App Theme",
    ("Light 🌞", "Dark 🌜"),
    index=0
)

if theme_choice == "Dark 🌜":
    st.markdown(
        """
        <style>
        body { background-color: #1E1E1E; color: #EEE; }
        .stApp { background-color: #1E1E1E; color: #EEE; }
        </style>
        """,
        unsafe_allow_html=True
    )

DEFAULT_SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"

st.sidebar.markdown("#### 1️⃣ Upload Google Service Account JSON")
auth_file = st.sidebar.file_uploader("Service Account JSON", type=["json"])

st.sidebar.markdown("#### 2️⃣ Google Sheet ID (already prefilled)")
sheet_id = st.sidebar.text_input(
    "Paste your Google Sheet ID here",
    value=DEFAULT_SHEET_ID
)

# Load Service Account credentials
gc = None
if auth_file and sheet_id:
    try:
        creds_dict = json.load(auth_file)
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        gc = gspread.authorize(creds)
        st.sidebar.success("✅ Google Authentication Successful!")
        st.sidebar.caption("You're ready to append data to your Google Sheet! 📈")
    except Exception as e:
        st.sidebar.error(f"❌ Auth Error: {e}")
else:
    st.sidebar.info("⚠️ Upload JSON & confirm Sheet ID to enable Google Sheets integration.")

st.sidebar.markdown("---")
st.sidebar.caption("✅ Built with ❤️ using Streamlit + Google Sheets.")

# ================================
# 📚 TABS / COLUMNS CONFIGURATION
# ================================
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

# ========================
# 📌 MAIN APP UI SECTION
# ========================
st.markdown("### ✅ Choose CRM Section (Tab)")
selected_tab = st.selectbox("Select the section you want to work with:", list(tabs_columns.keys()))
expected_columns = tabs_columns[selected_tab]

# -------------------------
st.markdown(f"<div class='section-header'>📤 Upload Existing CSV for: {selected_tab}</div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader(f"Upload your {selected_tab} CSV here", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("✅ CSV uploaded successfully!")
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")
        df = pd.DataFrame(columns=expected_columns)
else:
    df = pd.DataFrame(columns=expected_columns)

# -------------------------
st.markdown(f"<div class='section-header'>👀 Current Data for {selected_tab}</div>", unsafe_allow_html=True)
st.dataframe(df, use_container_width=True)

# -------------------------
st.markdown(f"<div class='section-header'>➕ Add New Entry to {selected_tab}</div>", unsafe_allow_html=True)
with st.form("add_entry_form"):
    new_data = {}
    cols = st.columns(len(expected_columns))
    for idx, col in enumerate(expected_columns):
        if col == "assessment_date":
            new_data[col] = datetime.date.today()
            cols[idx].text(f"{col}: {new_data[col]} (auto-filled)")
        else:
            new_data[col] = cols[idx].text_input(col, placeholder=f"Enter {col}")
    submitted = st.form_submit_button("Add Entry")
    if submitted:
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        st.success("✅ New entry added!")

# -------------------------
st.markdown(f"<div class='section-header'>⬇️ Download Updated {selected_tab} CSV</div>", unsafe_allow_html=True)
csv_data = df.to_csv(index=False)
st.download_button(
    label=f"📥 Download {selected_tab} CSV",
    data=csv_data,
    file_name=f"{selected_tab.lower().replace(' ','_')}.csv",
    mime='text/csv'
)

# -------------------------
if gc and sheet_id:
    st.markdown(f"<div class='section-header'>📡 Append New Entries to Google Sheet → **{selected_tab} Tab**</div>", unsafe_allow_html=True)
    st.markdown(
        """
        ✅ This will append only new rows in the current table to your Google Sheet tab.  
        ✅ If the tab doesn't exist, it will be created automatically.  
        """
    )
    if st.button(f"🚀 Append to Google Sheet Tab: {selected_tab}"):
        try:
            sh = gc.open_by_key(sheet_id)
            try:
                worksheet = sh.worksheet(selected_tab)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = sh.add_worksheet(title=selected_tab, rows="1000", cols="50")
                worksheet.append_row(expected_columns)  # Write headers

            # Get current records in the sheet (excluding header)
            existing_records = worksheet.get_all_values()
            if len(existing_records) > 1:
                existing_data = pd.DataFrame(existing_records[1:], columns=existing_records[0])
            else:
                existing_data = pd.DataFrame(columns=expected_columns)

            # Find new rows to append (those not already in sheet)
            if not df.empty:
                # Standardize columns for comparison
                for col in expected_columns:
                    if col not in df.columns:
                        df[col] = ""
                df = df[expected_columns]
                new_rows = df[~df.apply(tuple, 1).isin(existing_data.apply(tuple, 1))]
                if new_rows.empty:
                    st.info("No new data to append. All rows already exist in the sheet.")
                else:
                    for _, row in new_rows.iterrows():
                        worksheet.append_row([str(row.get(col, "")) for col in expected_columns])
                    st.success(f"✅ {len(new_rows)} new row(s) appended to Google Sheet tab: {selected_tab}!")
            else:
                st.warning("⚠️ No data to append. Please add or upload data first.")
        except Exception as e:
            st.error(f"❌ Google Sheets error: {e}")
else:
    st.info("ℹ️ Google Sheets append option will appear after you authenticate in the sidebar.")

# ========================
st.markdown("---")
st.caption("✅ One Google Sheet. Multiple Tabs. Professional CRM Profiles. Built with ❤️ in Streamlit.")
