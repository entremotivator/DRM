import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# ======= HARD CODED SHEET CONFIGURATION =======
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

# ======= LOAD DATA FROM SHEET =======
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
        # Ensure all expected columns are present
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""
        df = df[expected_columns]
        return df
    except Exception as e:
        st.error(f"❌ Could not load Google Sheet: {e}")
        return pd.DataFrame(columns=expected_columns)

# ======= SESSION STATE FOR DATAFRAME =======
if "df" not in st.session_state or st.session_state.get("last_tab") != selected_tab:
    st.session_state.df = load_gsheet_data()
    st.session_state.last_tab = selected_tab

df = st.session_state.df

# ======= DEMO DATA (if empty) =======
def get_demo_data():
    # 15 rows of realistic demo data (see previous answer for more)
    data = [
        ["Alice","Johnson","Alice Johnson","alice.j@acme.com","555-123-4567","ACME001","Technology","CTO",500,"acme.com","LinkedIn","2025-07-01"],
        ["Bob","Smith","Bob Smith","bob.smith@globex.net","555-234-5678","GLOBEX002","Manufacturing","Operations Manager",1200,"globex.net","Referral","2025-06-15"],
        ["Carol","Lee","Carol Lee","carol.lee@initech.org","555-345-6789","INIT003","Finance","CFO",300,"initech.org","Website","2025-07-10"],
        ["David","Kim","David Kim","dkim@umbrella.co","555-456-7890","UMBR004","Healthcare","HR Director",800,"umbrella.co","Conference","2025-07-05"],
        ["Eva","Martinez","Eva Martinez","eva.m@wayneenterprises.com","555-567-8901","WAYNE005","Retail","Sales Lead",2500,"wayneenterprises.com","LinkedIn","2025-06-20"],
        ["Frank","O'Neil","Frank O'Neil","foneil@starkind.com","555-678-9012","STARK006","Technology","Product Manager",150,"starkind.com","Cold Email","2025-07-12"],
        ["Grace","Patel","Grace Patel","grace.patel@oscorp.biz","555-789-0123","OSCORP007","Biotech","R&D Lead",600,"oscorp.biz","Referral","2025-07-13"],
        ["Henry","Wang","Henry Wang","henryw@bluthco.com","555-890-1234","BLUTH008","Real Estate","CEO",90,"bluthco.com","Event","2025-07-09"],
        ["Isabella","Rossi","Isabella Rossi","irossi@vandalay.com","555-901-2345","VAND009","Logistics","Supply Chain Dir",2000,"vandalay.com","Website","2025-07-11"],
        ["Jack","Müller","Jack Müller","jack.m@hooli.de","555-012-3456","HOOLI010","Technology","Data Scientist",3000,"hooli.de","LinkedIn","2025-07-13"],
        ["Karen","Silva","Karen Silva","karen.silva@wonka.com","555-112-2334","WONKA011","Food & Bev","Marketing Manager",400,"wonka.com","Referral","2025-07-02"],
        ["Leo","Dupont","Leo Dupont","l.dupont@dundermifflin.fr","555-223-3445","DUNDER012","Paper","Regional Manager",170,"dundermifflin.fr","Website","2025-07-07"],
        ["Mia","Chen","Mia Chen","mia.chen@massive.com","555-334-4556","MASS013","Media","Editor-in-Chief",800,"massive.com","LinkedIn","2025-07-04"],
        ["Noah","Brown","Noah Brown","noah.brown@prestige.com","555-445-5667","PREST014","Consulting","Managing Partner",60,"prestige.com","Conference","2025-07-06"],
        ["Olivia","Novak","Olivia Novak","olivia.novak@cyberdyne.ai","555-556-6778","CYBER015","AI","Lead Engineer",1200,"cyberdyne.ai","LinkedIn","2025-07-13"],
    ]
    return pd.DataFrame(data, columns=tabs_columns["Basic Info"])

if df.empty and selected_tab == "Basic Info":
    df = get_demo_data()
    st.session_state.df = df

# ======= CSV UPLOAD AND MERGE =======
uploaded_file = st.file_uploader(f"Upload {selected_tab} CSV to append:", type=["csv"])
if uploaded_file:
    try:
        new_df = pd.read_csv(uploaded_file)
        for col in expected_columns:
            if col not in new_df.columns:
                new_df[col] = ""
        new_df = new_df[expected_columns]
        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()
        st.session_state.df = df
        st.success("✅ CSV uploaded and merged!")
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
    reload_data=False
)

new_df = grid_response['data']
selected = grid_response['selected_rows']

# Save edits to session state
if not new_df.equals(df):
    st.session_state.df = new_df
    df = new_df
    st.success("✅ Table updated! (Don't forget to sync with Google Sheets below)")

# ======= DELETE ROW BUTTON =======
if selected:
    st.warning(f"Selected: {selected[0]}")
    if st.button("🗑️ Delete Selected Row"):
        idx = df.index[df['full_name'] == selected[0]['full_name']]
        df = df.drop(idx).reset_index(drop=True)
        st.session_state.df = df
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
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True).drop_duplicates()
        st.session_state.df = df
        st.success("✅ New entry added! (Don't forget to sync with Google Sheets below)")

# ======= DOWNLOAD CSV =======
csv_data = df.to_csv(index=False)
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
    sync_to_gsheet(df)

st.caption("✅ View, add, edit, select, and sync your CRM data. Built with ❤️ using Streamlit + Google Sheets + AgGrid.")

