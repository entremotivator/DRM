import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# ======= SHEET CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

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

# ======= SIDEBAR AUTHENTICATION =======
st.sidebar.header("🔑 Google Sheets Authentication")
auth_file = st.sidebar.file_uploader("Upload Service Account JSON", type=["json"])
gc = None
if auth_file:
    try:
        creds_dict = json.load(auth_file)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(creds)
        st.sidebar.success("✅ Google Authentication Successful!")
        st.sidebar.markdown(f"[Open Google Sheet]({SHEET_URL})")
    except Exception as e:
        st.sidebar.error(f"❌ Auth Error: {e}")
else:
    st.sidebar.info("⬆️ Upload your Google Service Account JSON to enable Sheets integration.")

st.sidebar.markdown("---")
st.sidebar.caption("Built with ❤️ using Streamlit + Google Sheets + AgGrid.")

# ======= MAIN APP =======
selected_tab = st.selectbox("Select CRM Section (Tab):", list(tabs_columns.keys()))
expected_columns = tabs_columns[selected_tab]

def load_gsheet_data():
    if not gc:
        return pd.DataFrame(columns=expected_columns)
    try:
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
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_columns]
        return df
    except Exception as e:
        st.error(f"❌ Could not load Google Sheet: {e}")
        return pd.DataFrame(columns=expected_columns)

# ======= ALWAYS LOAD LIVE DATA =======
if gc:
    df = load_gsheet_data()
else:
    st.warning("Authenticate with Google to load live data.")
    df = pd.DataFrame(columns=expected_columns)

# ======= CSV UPLOAD AND MERGE =======
uploaded_file = st.file_uploader(f"Upload {selected_tab} CSV to append:", type=["csv"], key="csv_"+selected_tab)
if uploaded_file:
    try:
        new_df = pd.read_csv(uploaded_file)
        for col in expected_columns:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[expected_columns]
        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()
        st.success("✅ CSV uploaded and merged! (Not yet saved to Google Sheets)")
    except Exception as e:
        st.error(f"❌ Error reading CSV: {e}")

# ======= AGGRID TABLE VIEW & EDITING =======
st.markdown("### 👀 Current Data (Editable Table)")
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_pagination(enabled=True)
gb.configure_default_column(editable=True, resizable=True)
gb.configure_selection(selection_mode="single", use_checkbox=True)
if "assessment_date" in expected_columns:
    gb.configure_column("assessment_date", editable=True, type=["dateColumnFilter","customDateTimeFormat"], custom_format_string='yyyy-MM-dd', pivot=True)
grid_options = gb.build()

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    height=500,
    reload_data=True  # Always reload from df, so always fresh!
)

edited_df = grid_response['data']
selected = grid_response['selected_rows']

# ======= DELETE ROW BUTTON =======
if selected:
    st.warning(f"Selected: {selected[0]}")
    if st.button("🗑️ Delete Selected Row"):
        idx = edited_df.index[edited_df['full_name'] == selected[0]['full_name']]
        edited_df = edited_df.drop(idx).reset_index(drop=True)
        st.success("Row deleted! (Don't forget to sync with Google Sheets below)")

# ======= ADD NEW ENTRY FORM =======
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
        edited_df = pd.concat([edited_df, pd.DataFrame([new_data])], ignore_index=True).drop_duplicates()
        st.success("✅ New entry added! (Don't forget to sync with Google Sheets below)")

# ======= DOWNLOAD CSV =======
csv_data = edited_df.to_csv(index=False)
st.download_button(
    label=f"📥 Download {selected_tab} CSV",
    data=csv_data,
    file_name=f"{selected_tab.lower().replace(' ','_')}.csv",
    mime='text/csv'
)

# ======= SYNC TO GOOGLE SHEETS =======
def sync_to_gsheet(df):
    if not gc:
        st.error("Google authentication required.")
        return
    try:
        sh = gc.open_by_key(SHEET_ID)
        try:
            worksheet = sh.worksheet(selected_tab)
            sh.del_worksheet(worksheet)
            worksheet = sh.add_worksheet(title=selected_tab, rows="1000", cols="50")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=selected_tab, rows="1000", cols="50")
        worksheet.update([expected_columns] + df.fillna("").astype(str).values.tolist())
        st.success(f"✅ Google Sheet '{selected_tab}' updated!")
        st.info(f"[Open your Google Sheet]({SHEET_URL})")
    except Exception as e:
        st.error(f"❌ Google Sheets error: {e}")

if st.button("🚀 Sync ALL Changes to Google Sheets (Overwrite Tab)"):
    sync_to_gsheet(edited_df)

st.caption("✅ Always showing live Google Sheets data. Edit, add, delete, and sync as needed. Built with ❤️ using Streamlit + Google Sheets + AgGrid.")
