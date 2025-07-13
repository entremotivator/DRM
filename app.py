import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
import time
import re

# ======= CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# All client fields as specified
CLIENT_FIELDS = [
    "first_name", "last_name", "full_name", "email", "timezone", "address_line_1", 
    "address_line_2", "city", "state", "postal_code", "country", "ip", "phone", 
    "source", "date_of_birth", "company_id", "discprofile", "discsales", 
    "disc_communiction", "leadership_style", "team_dynamics", "conflict_resolution", 
    "customer_service_approach", "decision_making_style", "workplace_behavior", 
    "hiring_and_recruitment", "_coaching_and_development"
]

# Field categories for better organization
FIELD_CATEGORIES = {
    "👤 Personal Information": [
        "first_name", "last_name", "full_name", "email", "phone", "date_of_birth", 
        "timezone", "ip", "source"
    ],
    "📍 Address Information": [
        "address_line_1", "address_line_2", "city", "state", "postal_code", "country"
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

# Field descriptions for better UX
FIELD_DESCRIPTIONS = {
    "first_name": "Client's first name",
    "last_name": "Client's last name", 
    "full_name": "Complete full name (auto-generated if empty)",
    "email": "Valid email address",
    "phone": "Phone number with country code",
    "date_of_birth": "Date of birth",
    "timezone": "Client's timezone (e.g., UTC-5, EST)",
    "ip": "IP address (optional)",
    "source": "How did you find this client?",
    "address_line_1": "Street address",
    "address_line_2": "Apartment, suite, etc.",
    "city": "City name",
    "state": "State or province",
    "postal_code": "ZIP or postal code",
    "country": "Country name",
    "company_id": "Company or organization name",
    "discprofile": "DISC personality profile",
    "discsales": "DISC sales approach",
    "disc_communiction": "DISC communication style",
    "leadership_style": "Leadership approach",
    "team_dynamics": "Team interaction style",
    "conflict_resolution": "Conflict resolution approach",
    "customer_service_approach": "Customer service style",
    "decision_making_style": "Decision making approach",
    "workplace_behavior": "Workplace behavior patterns",
    "hiring_and_recruitment": "Hiring and recruitment preferences",
    "_coaching_and_development": "Coaching and development needs"
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
    .form-header {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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
    .form-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4facfe;
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
    .error-container {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-container {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 10px;
        color: #262730;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ======= UTILITY FUNCTIONS =======
def safe_get(obj, key, default=""):
    """Safely get a value from object with default"""
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        elif hasattr(obj, key):
            return getattr(obj, key, default)
        else:
            return default
    except Exception:
        return default

def safe_str(value, default=""):
    """Safely convert value to string"""
    try:
        if pd.isna(value):
            return default
        return str(value).strip()
    except Exception:
        return default

def safe_len(obj):
    """Safely get length of object"""
    try:
        return len(obj) if obj is not None else 0
    except Exception:
        return 0

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number"""
    if not phone:
        return False
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    return len(digits_only) >= 7

def append_client_to_sheet(gc, client_data):
    """Append new client data to Google Sheet"""
    try:
        sh = gc.open_by_key(SHEET_ID)
        
        # Try to find the worksheet
        worksheet_names = ["Clients", "Client Data", "Sheet1", "Main", "Data"]
        worksheet = None
        
        for name in worksheet_names:
            try:
                worksheet = sh.worksheet(name)
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if not worksheet:
            # Use the first available worksheet
            all_worksheets = sh.worksheets()
            if all_worksheets:
                worksheet = all_worksheets[0]
            else:
                return False, "No worksheets found"
        
        # Get current headers
        try:
            headers = worksheet.row_values(1)
        except Exception:
            headers = CLIENT_FIELDS
            worksheet.append_row(headers)
        
        # Prepare row data
        row_data = []
        for field in headers:
            if field in client_data:
                value = client_data[field]
                if isinstance(value, datetime.date):
                    value = value.strftime('%Y-%m-%d')
                row_data.append(str(value) if value else "")
            else:
                row_data.append("")
        
        # Append the row
        worksheet.append_row(row_data)
        return True, "Client added successfully!"
        
    except Exception as e:
        return False, f"Error adding client: {str(e)}"

# ======= HEADER =======
try:
    st.markdown("""
    <div class="main-header">
        <h1 style='font-size:3em; margin:0;'>���� Live CRM Client Profiles</h1>
        <p style='font-size:1.2em; margin:0.5rem 0 0 0; opacity:0.9;'>
            Real-time Google Sheets Integration • Individual Client Profiles • Add New Clients
        </p>
    </div>
    """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error displaying header: {e}")

# ======= SIDEBAR AUTHENTICATION =======
try:
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
        auto_refresh = st.checkbox("Enable Auto-refresh", value=False)
        refresh_interval = 60
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
            if 'df' in st.session_state:
                del st.session_state['df']
            st.rerun()
        
        st.markdown("---")
        st.caption("Built with ❤️ using Streamlit")

except Exception as e:
    st.error(f"Error in sidebar: {e}")
    gc = None
    auto_refresh = False
    refresh_interval = 60

# ======= DATA LOADING FUNCTIONS =======
@st.cache_data(ttl=60)
def load_live_client_data():
    """Load live client data from Google Sheets with enhanced error handling"""
    if not gc:
        return pd.DataFrame(columns=CLIENT_FIELDS), "No authentication"
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        
        # Try to find a worksheet with client data
        worksheet_names = ["Clients", "Client Data", "Sheet1", "Main", "Data"]
        worksheet = None
        
        # Get all available worksheets
        try:
            all_worksheets = sh.worksheets()
            available_names = [ws.title for ws in all_worksheets]
            st.sidebar.info(f"Available sheets: {', '.join(available_names)}")
        except Exception:
            available_names = []
        
        # Try to find the right worksheet
        for name in worksheet_names:
            try:
                worksheet = sh.worksheet(name)
                st.sidebar.success(f"Using sheet: {name}")
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if not worksheet and all_worksheets:
            # Use the first available worksheet
            worksheet = all_worksheets[0]
            st.sidebar.warning(f"Using first available sheet: {worksheet.title}")
        
        if not worksheet:
            return pd.DataFrame(columns=CLIENT_FIELDS), "No worksheets found"
        
        # Get all data
        try:
            data = worksheet.get_all_values()
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error reading data: {e}"
        
        if not data:
            return pd.DataFrame(columns=CLIENT_FIELDS), "Sheet is empty"
        
        if len(data) < 2:
            return pd.DataFrame(columns=CLIENT_FIELDS), "No data rows found (only headers or empty)"
        
        # Create DataFrame
        try:
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            
            # Show available columns in sidebar
            st.sidebar.info(f"Available columns: {', '.join(headers[:10])}{'...' if len(headers) > 10 else ''}")
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error creating DataFrame: {e}"
        
        # Ensure all expected columns are present
        missing_columns = []
        for col in CLIENT_FIELDS:
            if col not in df.columns:
                df[col] = ""
                missing_columns.append(col)
        
        if missing_columns:
            st.sidebar.warning(f"Missing columns (added as empty): {', '.join(missing_columns[:5])}{'...' if len(missing_columns) > 5 else ''}")
        
        # Keep only the fields we want
        try:
            df = df[CLIENT_FIELDS].copy()
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error selecting columns: {e}"
        
        # Clean data
        df = clean_client_data(df)
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        return df, "Success"
        
    except Exception as e:
        error_msg = f"Error loading data: {str(e)[:200]}"
        return pd.DataFrame(columns=CLIENT_FIELDS), error_msg

def clean_client_data(df):
    """Clean and format client data with error handling"""
    if df.empty:
        return df
    
    try:
        df_clean = df.copy()
        
        # Clean email addresses
        if 'email' in df_clean.columns:
            try:
                df_clean['email'] = df_clean['email'].astype(str).str.lower().str.strip()
                # Remove invalid emails
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                df_clean.loc[~df_clean['email'].str.match(email_pattern, na=False), 'email'] = ''
            except Exception:
                pass
        
        # Clean phone numbers
        if 'phone' in df_clean.columns:
            try:
                df_clean['phone'] = df_clean['phone'].astype(str).str.strip()
                # Remove non-phone entries
                df_clean.loc[df_clean['phone'].str.len() < 7, 'phone'] = ''
            except Exception:
                pass
        
        # Format names
        name_fields = ['first_name', 'last_name', 'full_name']
        for field in name_fields:
            if field in df_clean.columns:
                try:
                    df_clean[field] = df_clean[field].astype(str).str.title().str.strip()
                    df_clean.loc[df_clean[field].isin(['Nan', 'None', 'Null', '']), field] = ''
                except Exception:
                    pass
        
        # Handle dates
        if 'date_of_birth' in df_clean.columns:
            try:
                df_clean['date_of_birth'] = pd.to_datetime(df_clean['date_of_birth'], errors='coerce')
            except Exception:
                pass
        
        return df_clean
    except Exception as e:
        st.error(f"Error cleaning data: {e}")
        return df

def get_client_completeness(client_data):
    """Calculate completeness percentage for a client with error handling"""
    try:
        total_fields = len(CLIENT_FIELDS)
        filled_fields = 0
        
        for field in CLIENT_FIELDS:
            value = safe_str(safe_get(client_data, field, ""))
            if value and value.lower() not in ['', 'nan', 'none', 'null']:
                filled_fields += 1
        
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0
    except Exception:
        return 0

def format_field_value(value, field_name):
    """Format field values for display with error handling"""
    try:
        value_str = safe_str(value)
        
        if not value_str or value_str.lower() in ['nan', 'none', 'null']:
            return '<span class="empty-value">Not provided</span>'
        
        # Special formatting for specific fields
        if field_name == 'email' and '@' in value_str:
            return f'<a href="mailto:{value_str}" target="_blank">{value_str}</a>'
        elif field_name == 'phone' and len(value_str) >= 7:
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
    except Exception:
        return '<span class="empty-value">Error displaying value</span>'

# ======= MAIN APPLICATION WITH TABS =======
try:
    # Initialize session state
    if 'df' not in st.session_state:
        st.session_state.df = pd.DataFrame(columns=CLIENT_FIELDS)
        st.session_state.load_status = "Not loaded"
        st.session_state.last_refresh = 0

    # Auto-refresh mechanism
    current_time = time.time()
    if auto_refresh and (current_time - st.session_state.last_refresh) > refresh_interval:
        st.cache_data.clear()
        if 'df' in st.session_state:
            del st.session_state['df']

    # Load data if not in session state or if refresh needed
    if 'df' not in st.session_state or st.session_state.df.empty:
        with st.spinner("🔄 Loading live client data..."):
            df, load_status = load_live_client_data()
            st.session_state.df = df
            st.session_state.load_status = load_status
            st.session_state.last_refresh = current_time
    else:
        df = st.session_state.df
        load_status = st.session_state.load_status

    # Display connection status and data info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            status = "🟢 Connected" if gc else "🔴 Disconnected"
            st.markdown(f"""
            <div class="metric-card">
                <h3>{status}</h3>
                <p>Google Sheets</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("Error displaying connection status")

    with col2:
        try:
            client_count = safe_len(df)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{client_count}</h3>
                <p>Total Clients</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("Error displaying client count")

    with col3:
        try:
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
        except Exception:
            st.error("Error calculating completeness")

    with col4:
        try:
            last_update = datetime.datetime.now().strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="metric-card">
                <h3>{last_update}</h3>
                <p>Last Updated</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.error("Error displaying timestamp")

    # Display load status
    if load_status != "Success":
        st.warning(f"⚠️ Data Loading Issue: {load_status}")

    # ======= TABS FOR DIFFERENT VIEWS =======
    tab1, tab2, tab3 = st.tabs(["👥 View Clients", "➕ Add New Client", "🔍 Debug Info"])

    # ======= TAB 1: VIEW CLIENTS =======
    with tab1:
        if df.empty:
            st.warning("📭 No client data found.")
            st.markdown("""
            ### 🔧 Troubleshooting Steps:
            1. **Check Authentication**: Upload your Google Service Account JSON file
            2. **Verify Sheet Access**: Ensure the service account has access to your sheet
            3. **Check Sheet Structure**: Your sheet should have headers in the first row
            4. **Verify Sheet Name**: Try naming your sheet 'Clients', 'Client Data', or 'Sheet1'
            5. **Check Data**: Ensure there are data rows below the headers
            
            ### 📋 Expected Column Names:
            """)
            # Display expected columns in a nice format
            cols = st.columns(3)
            for i, field in enumerate(CLIENT_FIELDS):
                with cols[i % 3]:
                    st.code(field)
        else:
            # ======= CLIENT SELECTION =======
            try:
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
                    available_sort_fields = [field for field in ["full_name", "email", "company_id", "first_name", "last_name"] if field in df.columns]
                    if available_sort_fields:
                        sort_by = st.selectbox(
                            "📊 Sort by:",
                            available_sort_fields,
                            format_func=lambda x: x.replace('_', ' ').title()
                        )
                    else:
                        sort_by = None
                
                # Filter clients based on search
                filtered_df = df.copy()
                if search_term:
                    try:
                        mask = df.astype(str).apply(
                            lambda x: x.str.contains(search_term, case=False, na=False)
                        ).any(axis=1)
                        filtered_df = df[mask]
                    except Exception as e:
                        st.warning(f"Search error: {e}")
                
                # Sort clients
                if sort_by and sort_by in filtered_df.columns:
                    try:
                        filtered_df = filtered_df.sort_values(sort_by)
                    except Exception as e:
                        st.warning(f"Sort error: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error in client selection: {e}")
                filtered_df = df.copy()

            # ======= CLIENT LIST =======
            if filtered_df.empty:
                st.info("🔍 No clients found matching your search criteria.")
            else:
                try:
                    st.subheader(f"👥 Client List ({len(filtered_df)} clients)")
                    
                    # Create client selection
                    client_options = []
                    for idx, row in filtered_df.iterrows():
                        try:
                            full_name = safe_str(safe_get(row, 'full_name', 'Unknown'))
                            email = safe_str(safe_get(row, 'email', 'No email'))
                            company = safe_str(safe_get(row, 'company_id', 'No company'))
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
                        except Exception as e:
                            st.warning(f"Error processing client at index {idx}: {e}")
                            continue
                    
                    # Client selection dropdown
                    if client_options:
                        try:
                            selected_option = st.selectbox(
                                "Select a client to view their profile:",
                                client_options,
                                format_func=lambda x: x[0]
                            )
                            
                            if selected_option:
                                selected_display, selected_idx = selected_option
                                
                                # ======= INDIVIDUAL CLIENT PROFILE =======
                                if selected_idx is not None and selected_idx in filtered_df.index:
                                    try:
                                        client_data = filtered_df.loc[selected_idx]
                                        
                                        # Profile header
                                        full_name = safe_str(safe_get(client_data, 'full_name', 'Unknown Client'))
                                        email = safe_str(safe_get(client_data, 'email', 'No email provided'))
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
                                            try:
                                                st.markdown(f"""
                                                <div class="field-section">
                                                    <h3 style='margin-top:0; color:#495057;'>{category}</h3>
                                                """, unsafe_allow_html=True)
                                                
                                                # Create field rows
                                                for field in fields:
                                                    if field in CLIENT_FIELDS:
                                                        try:
                                                            field_label = field.replace('_', ' ').title()
                                                            field_value = format_field_value(safe_get(client_data, field), field)
                                                            st.markdown(f"""
                                                            <div class="field-row">
                                                                <div class="field-label">{field_label}:</div>
                                                                <div class="field-value">{field_value}</div>
                                                            </div>
                                                            """, unsafe_allow_html=True)
                                                        except Exception as e:
                                                            st.warning(f"Error displaying field {field}: {e}")
                                                
                                                st.markdown('</div>', unsafe_allow_html=True)
                                            except Exception as e:
                                                st.error(f"Error displaying category {category}: {e}")
                                        
                                        # ======= PROFILE ACTIONS =======
                                        st.markdown("---")
                                        st.subheader("🔧 Profile Actions")
                                        
                                        action_col1, action_col2, action_col3 = st.columns(3)
                                        
                                        with action_col1:
                                            if st.button("📧 Send Email", key="send_email"):
                                                email_addr = safe_str(safe_get(client_data, 'email', ''))
                                                if email_addr and '@' in email_addr:
                                                    st.success(f"📧 Email client: {email_addr}")
                                                    st.markdown(f'<a href="mailto:{email_addr}" target="_blank">Open Email Client</a>', unsafe_allow_html=True)
                                                else:
                                                    st.warning("❌ No valid email address available")
                                        
                                        with action_col2:
                                            if st.button("📞 Call Client", key="call_client"):
                                                phone = safe_str(safe_get(client_data, 'phone', ''))
                                                if phone and len(phone) >= 7:
                                                    st.success(f"📞 Call client: {phone}")
                                                    st.markdown(f'<a href="tel:{phone}">Call Now</a>', unsafe_allow_html=True)
                                                else:
                                                    st.warning("❌ No valid phone number available")
                                        
                                        with action_col3:
                                            if st.button("📝 Edit Profile", key="edit_profile"):
                                                st.info("📝 Edit functionality - Coming soon!")
                                        
                                        # ======= EXPORT CLIENT DATA =======
                                        st.markdown("---")
                                        st.subheader("📥 Export Client Data")
                                        
                                        try:
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
                                        except Exception as e:
                                            st.error(f"Export error: {e}")
                                        
                                    except Exception as e:
                                        st.error(f"Error displaying client profile: {e}")
                                else:
                                    st.error("Selected client not found in data")
                        except Exception as e:
                            st.error(f"Error in client selection: {e}")
                    else:
                        st.warning("No valid client options available")
                except Exception as e:
                    st.error(f"Error creating client list: {e}")

    # ======= TAB 2: ADD NEW CLIENT =======
    with tab2:
        st.markdown("""
        <div class="form-header">
            <h1 style='margin:0; font-size:2.5em;'>➕ Add New Client</h1>
            <p style='margin:0.5rem 0 0 0; font-size:1.2em; opacity:0.9;'>
                Fill out the form below to add a new client to your CRM
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not gc:
            st.error("❌ Please authenticate with Google Sheets first (upload JSON file in sidebar)")
        else:
            with st.form("add_client_form", clear_on_submit=True):
                st.subheader("📝 Client Information")
                
                # Initialize form data
                form_data = {}
                
                # Create form sections by category
                for category, fields in FIELD_CATEGORIES.items():
                    st.markdown(f"""
                    <div class="form-section">
                        <h3 style='margin-top:0; color:#495057;'>{category}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create columns for better layout
                    if len(fields) > 1:
                        cols = st.columns(2)
                    else:
                        cols = [st]
                    
                    for i, field in enumerate(fields):
                        with cols[i % len(cols)] if len(cols) > 1 else cols[0]:
                            field_label = field.replace('_', ' ').title()
                            field_help = FIELD_DESCRIPTIONS.get(field, f"Enter {field_label.lower()}")
                            
                            # Special input types for specific fields
                            if field == 'email':
                                form_data[field] = st.text_input(
                                    field_label,
                                    placeholder="example@email.com",
                                    help=field_help
                                )
                            elif field == 'phone':
                                form_data[field] = st.text_input(
                                    field_label,
                                    placeholder="+1-555-123-4567",
                                    help=field_help
                                )
                            elif field == 'date_of_birth':
                                form_data[field] = st.date_input(
                                    field_label,
                                    value=None,
                                    help=field_help,
                                    min_value=datetime.date(1900, 1, 1),
                                    max_value=datetime.date.today()
                                )
                            elif field in ['discprofile', 'discsales', 'disc_communiction', 'leadership_style']:
                                form_data[field] = st.selectbox(
                                    field_label,
                                    options=['', 'D - Dominant', 'I - Influential', 'S - Steady', 'C - Conscientious'],
                                    help=field_help
                                )
                            elif field == 'source':
                                form_data[field] = st.selectbox(
                                    field_label,
                                    options=['', 'Website', 'Referral', 'Social Media', 'Email Campaign', 'Cold Call', 'Event', 'Other'],
                                    help=field_help
                                )
                            elif field == 'country':
                                form_data[field] = st.selectbox(
                                    field_label,
                                    options=['', 'United States', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France', 'Other'],
                                    help=field_help
                                )
                            elif field in ['team_dynamics', 'conflict_resolution', 'customer_service_approach', 
                                         'decision_making_style', 'workplace_behavior', 'hiring_and_recruitment', 
                                         '_coaching_and_development']:
                                form_data[field] = st.text_area(
                                    field_label,
                                    height=100,
                                    help=field_help
                                )
                            else:
                                form_data[field] = st.text_input(
                                    field_label,
                                    help=field_help
                                )
                
                # Form submission
                st.markdown("---")
                submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
                
                with submit_col2:
                    submitted = st.form_submit_button(
                        "➕ Add Client to CRM",
                        use_container_width=True,
                        type="primary"
                    )
                
                if submitted:
                    # Validate required fields
                    errors = []
                    
                    # Check for required fields
                    if not form_data.get('first_name', '').strip():
                        errors.append("First name is required")
                    if not form_data.get('last_name', '').strip():
                        errors.append("Last name is required")
                    if not form_data.get('email', '').strip():
                        errors.append("Email is required")
                    
                    # Validate email format
                    if form_data.get('email', '').strip() and not validate_email(form_data['email']):
                        errors.append("Please enter a valid email address")
                    
                    # Validate phone if provided
                    if form_data.get('phone', '').strip() and not validate_phone(form_data['phone']):
                        errors.append("Please enter a valid phone number")
                    
                    if errors:
                        st.error("❌ Please fix the following errors:")
                        for error in errors:
                            st.error(f"• {error}")
                    else:
                        # Auto-generate full name if not provided
                        if not form_data.get('full_name', '').strip():
                            first_name = form_data.get('first_name', '').strip()
                            last_name = form_data.get('last_name', '').strip()
                            form_data['full_name'] = f"{first_name} {last_name}".strip()
                        
                        # Clean and prepare data
                        clean_data = {}
                        for field in CLIENT_FIELDS:
                            value = form_data.get(field, '')
                            if isinstance(value, str):
                                value = value.strip()
                            clean_data[field] = value
                        
                        # Add to Google Sheet
                        with st.spinner("Adding client to Google Sheets..."):
                            success, message = append_client_to_sheet(gc, clean_data)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            
                            # Clear cache to refresh data
                            st.cache_data.clear()
                            if 'df' in st.session_state:
                                del st.session_state['df']
                            
                            # Show success message with client info
                            st.info(f"🎉 Successfully added {clean_data['full_name']} to your CRM!")
                            
                            # Option to add another client
                            if st.button("➕ Add Another Client"):
                                st.rerun()
                        else:
                            st.error(f"❌ {message}")

    # ======= TAB 3: DEBUG INFO =======
    with tab3:
        st.subheader("🔍 Debug Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Connection Status:**")
            st.write(f"• Authentication: {'✅ Connected' if gc else '❌ Not Connected'}")
            st.write(f"• Load Status: {load_status}")
            st.write(f"• Auto Refresh: {'✅ Enabled' if auto_refresh else '❌ Disabled'}")
            st.write(f"• Refresh Interval: {refresh_interval}s")
            
            st.write("**Data Information:**")
            st.write(f"• DataFrame Shape: {df.shape if not df.empty else 'Empty'}")
            st.write(f"• Total Clients: {len(df)}")
            st.write(f"• Last Refresh: {datetime.datetime.fromtimestamp(st.session_state.last_refresh).strftime('%H:%M:%S') if st.session_state.last_refresh > 0 else 'Never'}")
        
        with col2:
            st.write("**Expected Fields:**")
            for field in CLIENT_FIELDS[:15]:  # Show first 15 fields
                st.code(field)
            if len(CLIENT_FIELDS) > 15:
                st.write(f"... and {len(CLIENT_FIELDS) - 15} more fields")
        
        if not df.empty:
            st.write("**Sample Data:**")
            st.dataframe(df.head(3))
            
            st.write("**Data Types:**")
            st.write(df.dtypes)

except Exception as e:
    st.error(f"❌ Critical Application Error: {e}")
    st.info("Please refresh the page and try again. If the issue persists, check your data and authentication.")

# ======= FOOTER =======
try:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>Live CRM Client Profiles</strong></p>
        <p>🔄 Real-time Google Sheets Integration • 👥 Individual Client Views • ➕ Add New Clients</p>
        <p>Built with ❤️ using Streamlit + Google Sheets API</p>
    </div>
    """, unsafe_allow_html=True)
except Exception:
    st.write("Live CRM Client Profiles - Built with Streamlit")
