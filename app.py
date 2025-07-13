import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
import time

# ======= CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# All client fields as specified
CLIENT_FIELDS = [
    "first_name",
    "last_name", 
    "full_name",
    "email",
    "timezone",
    "address_line_1",
    "address_line_2",
    "city",
    "state",
    "postal_code",
    "country",
    "ip",
    "phone",
    "source",
    "date_of_birth",
    "company_id",
    "discprofile",
    "discsales",
    "disc_communiction",
    "leadership_style",
    "team_dynamics",
    "conflict_resolution",
    "customer_service_approach",
    "decision_making_style",
    "workplace_behavior",
    "hiring_and_recruitment",
    "_coaching_and_development"
]

# Field categories for better organization
FIELD_CATEGORIES = {
    "👤 Personal Information": [
        "first_name", "last_name", "full_name", "email", "phone", 
        "date_of_birth", "timezone", "ip", "source"
    ],
    "📍 Address Information": [
        "address_line_1", "address_line_2", "city", "state", 
        "postal_code", "country"
    ],
    "🏢 Company Information": [
        "company_id"
    ],
    "🧠 DISC Profiles": [
        "discprofile", "discsales", "disc_communiction", "leadership_style",
        "team_dynamics", "conflict_resolution", "customer_service_approach",
        "decision_making_style", "workplace_behavior"
    ],
    "📚 HR & Development": [
        "hiring_and_recruitment", "_coaching_and_development"
    ]
}

# ======= PAGE CONFIGURATION =======
st.set_page_config(
    page_title="Live CRM Client Profiles", 
    layout="wide", 
    page_icon="👥",
    initial_sidebar_state="expanded"
)

# ======= CUSTOM CSS =======
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .client-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        transition: transform 0.2s ease;
    }
    
    .client-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }
    
    .profile-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .field-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .field-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e9ecef;
    }
    
    .field-label {
        font-weight: 600;
        color: #495057;
        min-width: 200px;
    }
    
    .field-value {
        color: #212529;
        flex: 1;
        text-align: right;
    }
    
    .empty-value {
        color: #6c757d;
        font-style: italic;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online { background-color: #28a745; }
    .status-offline { background-color: #dc3545; }
    .status-partial { background-color: #ffc107; }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #667eea;
    }
    
    .search-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ======= HEADER =======
st.markdown("""
<div class="main-header">
    <h1 style='font-size:3em; margin:0;'>👥 Live CRM Client Profiles</h1>
    <p style='font-size:1.2em; margin:0.5rem 0 0 0; opacity:0.9;'>
        Real-time Google Sheets Integration • Individual Client Profiles
    </p>
</div>
""", unsafe_allow_html=True)

# ======= SIDEBAR AUTHENTICATION =======
with st.sidebar:
    st.header("🔑 Authentication")
    auth_file = st.file_uploader("Upload Service Account JSON", type=["json"])
    
    gc = None
    if auth_file:
        try:
            creds_dict = json.load(auth_file)
            creds = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            gc = gspread.authorize(creds)
            st.success("✅ Connected to Google Sheets!")
            st.markdown(f"[📊 Open Sheet]({SHEET_URL})")
        except Exception as e:
            st.error(f"❌ Auth Error: {str(e)[:100]}...")
    else:
        st.info("⬆️ Upload your Google Service Account JSON")
    
    st.markdown("---")
    
    # Auto-refresh settings
    st.header("🔄 Live Updates")
    auto_refresh = st.checkbox("Enable Auto-refresh", value=True)
    if auto_refresh:
        refresh_interval = st.selectbox(
            "Refresh Interval:",
            [30, 60, 120, 300],
            index=1,
            format_func=lambda x: f"{x} seconds"
        )
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit")

# ======= UTILITY FUNCTIONS =======
@st.cache_data(ttl=60)  # Cache for 1 minute for live updates
def load_live_client_data():
    """Load live client data from Google Sheets"""
    if not gc:
        return pd.DataFrame(columns=CLIENT_FIELDS)
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        
        # Try to find a worksheet with client data
        worksheet_names = ["Clients", "Client Data", "Sheet1", "Main"]
        worksheet = None
        
        for name in worksheet_names:
            try:
                worksheet = sh.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if not worksheet:
            # Use the first available worksheet
            worksheets = sh.worksheets()
            if worksheets:
                worksheet = worksheets[0]
            else:
                return pd.DataFrame(columns=CLIENT_FIELDS)
        
        # Get all data
        data = worksheet.get_all_values()
        
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.DataFrame(columns=CLIENT_FIELDS)
        
        # Ensure all expected columns are present
        for col in CLIENT_FIELDS:
            if col not in df.columns:
                df[col] = ""
        
        # Keep only the fields we want and clean data
        df = df[CLIENT_FIELDS].copy()
        
        # Clean and format data
        df = clean_client_data(df)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame(columns=CLIENT_FIELDS)

def clean_client_data(df):
    """Clean and format client data"""
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    # Clean email addresses
    if 'email' in df_clean.columns:
        df_clean['email'] = df_clean['email'].astype(str).str.lower().str.strip()
    
    # Clean phone numbers
    if 'phone' in df_clean.columns:
        df_clean['phone'] = df_clean['phone'].astype(str).str.strip()
    
    # Format names
    name_fields = ['first_name', 'last_name', 'full_name']
    for field in name_fields:
        if field in df_clean.columns:
            df_clean[field] = df_clean[field].astype(str).str.title().str.strip()
    
    # Handle dates
    if 'date_of_birth' in df_clean.columns:
        df_clean['date_of_birth'] = pd.to_datetime(df_clean['date_of_birth'], errors='coerce')
    
    # Remove completely empty rows
    df_clean = df_clean.dropna(how='all')
    
    return df_clean

def get_client_completeness(client_data):
    """Calculate completeness percentage for a client"""
    total_fields = len(CLIENT_FIELDS)
    filled_fields = 0
    
    for field in CLIENT_FIELDS:
        value = str(client_data.get(field, "")).strip()
        if value and value.lower() not in ['', 'nan', 'none', 'null']:
            filled_fields += 1
    
    return (filled_fields / total_fields) * 100

def format_field_value(value, field_name):
    """Format field values for display"""
    if pd.isna(value) or str(value).strip() in ['', 'nan', 'None', 'null']:
        return '<span class="empty-value">Not provided</span>'
    
    value_str = str(value).strip()
    
    # Special formatting for specific fields
    if field_name == 'email':
        return f'<a href="mailto:{value_str}">{value_str}</a>'
    elif field_name == 'phone':
        return f'<a href="tel:{value_str}">{value_str}</a>'
    elif field_name == 'date_of_birth':
        try:
            date_obj = pd.to_datetime(value_str)
            return date_obj.strftime('%B %d, %Y')
        except:
            return value_str
    elif 'address' in field_name or field_name in ['city', 'state', 'country']:
        return value_str.title()
    else:
        return value_str

# ======= MAIN APPLICATION =======

# Load live data
with st.spinner("🔄 Loading live client data..."):
    df = load_live_client_data()

# Auto-refresh mechanism
if auto_refresh and 'last_refresh' in st.session_state:
    time_since_refresh = time.time() - st.session_state.last_refresh
    if time_since_refresh > refresh_interval:
        st.cache_data.clear()
        st.rerun()

st.session_state.last_refresh = time.time()

# Display connection status and data info
col1, col2, col3, col4 = st.columns(4)

with col1:
    status = "🟢 Connected" if gc else "🔴 Disconnected"
    st.markdown(f"""
    <div class="metric-card">
        <h3>{status}</h3>
        <p>Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{len(df)}</h3>
        <p>Total Clients</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    if not df.empty:
        avg_completeness = df.apply(lambda row: get_client_completeness(row), axis=1).mean()
    else:
        avg_completeness = 0
    st.markdown(f"""
    <div class="metric-card">
        <h3>{avg_completeness:.1f}%</h3>
        <p>Avg Completeness</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    last_update = datetime.datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="metric-card">
        <h3>{last_update}</h3>
        <p>Last Updated</p>
    </div>
    """, unsafe_allow_html=True)

if df.empty:
    st.warning("📭 No client data found. Please check your Google Sheet and authentication.")
    st.info("""
    **Setup Instructions:**
    1. Upload your Google Service Account JSON file
    2. Ensure your sheet contains client data with the specified field names
    3. The sheet should be named 'Clients', 'Client Data', or be the first sheet
    """)
else:
    # ======= CLIENT SELECTION =======
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.subheader("🔍 Select Client Profile")
    
    # Search and filter options
    search_col1, search_col2 = st.columns([2, 1])
    
    with search_col1:
        search_term = st.text_input(
            "🔎 Search clients:",
            placeholder="Search by name, email, company...",
            help="Search across all client fields"
        )
    
    with search_col2:
        sort_by = st.selectbox(
            "📊 Sort by:",
            ["full_name", "email", "company_id", "first_name", "last_name"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    # Filter clients based on search
    filtered_df = df.copy()
    
    if search_term:
        mask = df.astype(str).apply(
            lambda x: x.str.contains(search_term, case=False, na=False)
        ).any(axis=1)
        filtered_df = df[mask]
    
    # Sort clients
    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ======= CLIENT LIST =======
    if filtered_df.empty:
        st.info("🔍 No clients found matching your search criteria.")
    else:
        st.subheader(f"👥 Client List ({len(filtered_df)} clients)")
        
        # Create client selection
        client_options = []
        for idx, row in filtered_df.iterrows():
            full_name = row.get('full_name', 'Unknown')
            email = row.get('email', 'No email')
            company = row.get('company_id', 'No company')
            completeness = get_client_completeness(row)
            
            # Status indicator based on completeness
            if completeness >= 80:
                status = "🟢"
            elif completeness >= 50:
                status = "🟡"
            else:
                status = "🔴"
            
            display_text = f"{status} {full_name} ({email}) - {company} [{completeness:.0f}% complete]"
            client_options.append((display_text, idx))
        
        # Client selection dropdown
        if client_options:
            selected_display, selected_idx = st.selectbox(
                "Select a client to view their profile:",
                client_options,
                format_func=lambda x: x[0]
            )
            
            # ======= INDIVIDUAL CLIENT PROFILE =======
            if selected_idx is not None:
                client_data = filtered_df.loc[selected_idx]
                
                # Profile header
                full_name = client_data.get('full_name', 'Unknown Client')
                email = client_data.get('email', 'No email provided')
                completeness = get_client_completeness(client_data)
                
                st.markdown(f"""
                <div class="profile-header">
                    <h1 style='margin:0; font-size:2.5em;'>{full_name}</h1>
                    <p style='margin:0.5rem 0 0 0; font-size:1.2em; opacity:0.9;'>{email}</p>
                    <p style='margin:0.5rem 0 0 0; font-size:1em; opacity:0.8;'>Profile Completeness: {completeness:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display fields by category
                for category, fields in FIELD_CATEGORIES.items():
                    st.markdown(f"""
                    <div class="field-section">
                        <h3 style='margin-top:0; color:#495057;'>{category}</h3>
                    """, unsafe_allow_html=True)
                    
                    # Create field rows
                    for field in fields:
                        if field in CLIENT_FIELDS:
                            field_label = field.replace('_', ' ').title()
                            field_value = format_field_value(client_data.get(field), field)
                            
                            st.markdown(f"""
                            <div class="field-row">
                                <div class="field-label">{field_label}:</div>
                                <div class="field-value">{field_value}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # ======= PROFILE ACTIONS =======
                st.markdown("---")
                st.subheader("🔧 Profile Actions")
                
                action_col1, action_col2, action_col3 = st.columns(3)
                
                with action_col1:
                    if st.button("📧 Send Email", key="send_email"):
                        email_addr = client_data.get('email', '')
                        if email_addr:
                            st.success(f"Email client would open to: {email_addr}")
                        else:
                            st.warning("No email address available")
                
                with action_col2:
                    if st.button("📞 Call Client", key="call_client"):
                        phone = client_data.get('phone', '')
                        if phone:
                            st.success(f"Phone dialer would open: {phone}")
                        else:
                            st.warning("No phone number available")
                
                with action_col3:
                    if st.button("📝 Edit Profile", key="edit_profile"):
                        st.info("Edit functionality would open here")
                
                # ======= EXPORT CLIENT DATA =======
                st.markdown("---")
                st.subheader("📥 Export Client Data")
                
                # Prepare client data for export
                client_export_data = pd.DataFrame([client_data])
                
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    csv_data = client_export_data.to_csv(index=False)
                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv_data,
                        file_name=f"{full_name.replace(' ', '_')}_profile.csv",
                        mime='text/csv'
                    )
                
                with export_col2:
                    json_data = client_export_data.to_json(orient='records', indent=2)
                    st.download_button(
                        label="🔗 Download as JSON",
                        data=json_data,
                        file_name=f"{full_name.replace(' ', '_')}_profile.json",
                        mime='application/json'
                    )

# ======= FOOTER =======
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Live CRM Client Profiles</strong></p>
    <p>🔄 Real-time Google Sheets Integration • 👥 Individual Client Views</p>
    <p>Built with ❤️ using Streamlit + Google Sheets API</p>
</div>
""", unsafe_allow_html=True)
