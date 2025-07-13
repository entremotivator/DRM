"""
HRDISCCRM - HR DISC CRM Application
Enhanced Streamlit application for managing client profiles with improved CSV handling,
append/edit functionalities, and light theme design.
"""

# ======= IMPORTS =======
import streamlit as st
import pandas as pd
import datetime
import gspread
import json
import time
import re
import io
import csv
from typing import Dict, List, Optional, Tuple, Any
from google.oauth2.service_account import Credentials

# ======= CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# All client fields as specified
CLIENT_FIELDS = [
    "first_name", "last_name", "full_name", "email", "timezone",
    "address_line_1", "address_line_2", "city", "state", "postal_code", "country",
    "ip", "phone", "source", "date_of_birth", "company_id", "discprofile",
    "discsales", "disc_communiction", "leadership_style", "team_dynamics",
    "conflict_resolution", "customer_service_approach", "decision_making_style",
    "workplace_behavior", "hiring_and_recruitment", "_coaching_and_development"
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

# Large text fields that need special CSV handling
LARGE_TEXT_FIELDS = [
    "discprofile", "discsales", "disc_communiction", "leadership_style",
    "team_dynamics", "conflict_resolution", "customer_service_approach",
    "decision_making_style", "workplace_behavior", "hiring_and_recruitment",
    "_coaching_and_development"
]

# ======= PAGE CONFIGURATION =======
st.set_page_config(
    page_title="HRDISCCRM - HR DISC Client Management",
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# ======= LIGHT THEME CSS =======
st.markdown("""
<style>
    /* Light theme with dark text */
    .stApp {
        background-color: #ffffff;
        color: #2c3e50;
    }
    
    .main-header {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(52, 152, 219, 0.3);
    }
    
    .client-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #3498db;
        margin: 1rem 0;
        transition: all 0.3s ease;
        color: #2c3e50;
    }
    
    .client-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    }
    
    .profile-header {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(231, 76, 60, 0.3);
    }
    
    .field-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
        color: #2c3e50;
    }
    
    .field-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 0.75rem 0;
        border-bottom: 1px solid #ecf0f1;
    }
    
    .field-label {
        font-weight: 600;
        color: #34495e;
        min-width: 200px;
        margin-right: 1rem;
    }
    
    .field-value {
        color: #2c3e50;
        flex: 1;
        text-align: left;
        word-wrap: break-word;
        white-space: pre-wrap;
        max-width: 400px;
    }
    
    .large-text-value {
        background: #ffffff;
        padding: 0.5rem;
        border-radius: 5px;
        border: 1px solid #bdc3c7;
        font-size: 0.9em;
        line-height: 1.4;
    }
    
    .empty-value {
        color: #95a5a6;
        font-style: italic;
    }
    
    .metric-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        text-align: center;
        border-top: 4px solid #3498db;
        color: #2c3e50;
    }
    
    .search-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
        border: 1px solid #ecf0f1;
    }
    
    .edit-form {
        background: #ffffff;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #ecf0f1;
        margin: 1rem 0;
    }
    
    .success-message {
        background: #d5f4e6;
        border: 1px solid #27ae60;
        color: #27ae60;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #fadbd8;
        border: 1px solid #e74c3c;
        color: #e74c3c;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fef9e7;
        border: 1px solid #f39c12;
        color: #f39c12;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Streamlit component styling */
    .stSelectbox > div > div {
        background-color: #ffffff;
        color: #2c3e50;
    }
    
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
</style>
""", unsafe_allow_html=True)

# ======= UTILITY FUNCTIONS =======
def safe_get(obj: Any, key: str, default: str = "") -> str:
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

def safe_str(value: Any, default: str = "") -> str:
    """Safely convert value to string with proper handling for large text"""
    try:
        if pd.isna(value):
            return default
        result = str(value).strip()
        # Handle large text fields - preserve formatting
        if len(result) > 100:
            return result
        return result
    except Exception:
        return default

def safe_len(obj: Any) -> int:
    """Safely get length of object"""
    try:
        return len(obj) if obj is not None else 0
    except Exception:
        return 0

def clean_csv_text(text: str) -> str:
    """Clean text for CSV export, handling large paragraphs properly"""
    if not text:
        return ""
    
    # Remove problematic characters but preserve formatting
    text = str(text).strip()
    # Replace problematic quotes
    text = text.replace('"', '""')
    # Preserve line breaks for large text
    return text

def export_to_csv_enhanced(df: pd.DataFrame) -> str:
    """Enhanced CSV export with proper handling of large text fields"""
    output = io.StringIO()
    
    # Custom CSV writer with proper quoting for large text
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator='\n')
    
    # Write headers
    writer.writerow(df.columns.tolist())
    
    # Write data rows with special handling for large text
    for _, row in df.iterrows():
        cleaned_row = []
        for col in df.columns:
            value = row[col]
            if col in LARGE_TEXT_FIELDS:
                # Special handling for large text fields
                cleaned_value = clean_csv_text(value)
            else:
                cleaned_value = safe_str(value)
            cleaned_row.append(cleaned_value)
        writer.writerow(cleaned_row)
    
    return output.getvalue()

# ======= AUTHENTICATION FUNCTIONS =======
def setup_google_sheets_connection() -> Optional[gspread.Client]:
    """Setup Google Sheets connection with enhanced error handling"""
    try:
        with st.sidebar:
            st.header("🔑 Authentication")
            auth_file = st.file_uploader("Upload Service Account JSON", type=["json"])
            
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
                    return gc
                except Exception as e:
                    st.error(f"❌ Auth Error: {str(e)[:100]}...")
                    return None
            else:
                st.info("⬆️ Upload your Google Service Account JSON")
                return None
    except Exception as e:
        st.error(f"Error in authentication setup: {e}")
        return None

# ======= DATA LOADING FUNCTIONS =======
@st.cache_data(ttl=60)
def load_live_client_data(gc_available: bool) -> Tuple[pd.DataFrame, str]:
    """Load live client data from Google Sheets with enhanced error handling"""
    if not gc_available:
        return pd.DataFrame(columns=CLIENT_FIELDS), "No authentication"
    
    try:
        # Get the Google Sheets client from session state
        gc = st.session_state.get('gc')
        if not gc:
            return pd.DataFrame(columns=CLIENT_FIELDS), "No Google Sheets connection"
        
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

def clean_client_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and format client data with enhanced handling for large text fields"""
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
        
        # Handle large text fields - preserve formatting
        for field in LARGE_TEXT_FIELDS:
            if field in df_clean.columns:
                try:
                    df_clean[field] = df_clean[field].astype(str)
                    # Clean but preserve paragraph structure
                    df_clean[field] = df_clean[field].apply(lambda x: x.strip() if x and x != 'nan' else '')
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

def get_client_completeness(client_data: pd.Series) -> float:
    """Calculate completeness percentage for a client"""
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

def format_field_value(value: Any, field_name: str) -> str:
    """Format field values for display with enhanced handling for large text"""
    try:
        value_str = safe_str(value)
        
        if not value_str or value_str.lower() in ['nan', 'none', 'null']:
            return '<span class="empty-value">Not provided</span>'
        
        # Special formatting for large text fields
        if field_name in LARGE_TEXT_FIELDS and len(value_str) > 50:
            # Truncate for display but show full text in expandable section
            truncated = value_str[:100] + "..." if len(value_str) > 100 else value_str
            return f'<div class="large-text-value">{truncated}</div>'
        
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

# ======= CRUD FUNCTIONS =======
def add_new_client(gc: gspread.Client, client_data: Dict[str, str]) -> Tuple[bool, str]:
    """Add a new client to the Google Sheet"""
    try:
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.worksheet("Clients")  # Assuming "Clients" sheet exists
        
        # Prepare row data in the correct order
        row_data = []
        for field in CLIENT_FIELDS:
            value = client_data.get(field, "")
            # Handle large text fields properly
            if field in LARGE_TEXT_FIELDS:
                value = clean_csv_text(value)
            row_data.append(value)
        
        # Append the row
        worksheet.append_row(row_data)
        return True, "Client added successfully!"
        
    except Exception as e:
        return False, f"Error adding client: {str(e)}"

def update_client(gc: gspread.Client, row_index: int, client_data: Dict[str, str]) -> Tuple[bool, str]:
    """Update an existing client in the Google Sheet"""
    try:
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.worksheet("Clients")
        
        # Prepare row data in the correct order
        row_data = []
        for field in CLIENT_FIELDS:
            value = client_data.get(field, "")
            # Handle large text fields properly
            if field in LARGE_TEXT_FIELDS:
                value = clean_csv_text(value)
            row_data.append(value)
        
        # Update the row (row_index + 2 because of 0-indexing and header row)
        worksheet.update(f"A{row_index + 2}:Z{row_index + 2}", [row_data])
        return True, "Client updated successfully!"
        
    except Exception as e:
        return False, f"Error updating client: {str(e)}"

# ======= UI COMPONENTS =======
def render_client_form(client_data: Optional[Dict[str, str]] = None, mode: str = "add") -> Optional[Dict[str, str]]:
    """Render client form for adding or editing"""
    st.subheader(f"{'✏️ Edit Client' if mode == 'edit' else '➕ Add New Client'}")
    
    form_data = {}
    
    with st.form(f"{mode}_client_form"):
        # Organize form by categories
        for category, fields in FIELD_CATEGORIES.items():
            st.markdown(f"**{category}**")
            
            cols = st.columns(2)
            for i, field in enumerate(fields):
                if field in CLIENT_FIELDS:
                    col = cols[i % 2]
                    
                    with col:
                        field_label = field.replace('_', ' ').title()
                        current_value = client_data.get(field, "") if client_data else ""
                        
                        # Use text area for large text fields
                        if field in LARGE_TEXT_FIELDS:
                            form_data[field] = st.text_area(
                                field_label,
                                value=current_value,
                                height=100,
                                help=f"Enter detailed {field_label.lower()}"
                            )
                        elif field == 'email':
                            form_data[field] = st.text_input(
                                field_label,
                                value=current_value,
                                placeholder="user@example.com"
                            )
                        elif field == 'phone':
                            form_data[field] = st.text_input(
                                field_label,
                                value=current_value,
                                placeholder="+1-555-123-4567"
                            )
                        elif field == 'date_of_birth':
                            if current_value:
                                try:
                                    default_date = pd.to_datetime(current_value).date()
                                except:
                                    default_date = None
                            else:
                                default_date = None
                            
                            form_data[field] = st.date_input(
                                field_label,
                                value=default_date
                            )
                        else:
                            form_data[field] = st.text_input(
                                field_label,
                                value=current_value
                            )
            
            st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button(
            f"{'💾 Update Client' if mode == 'edit' else '➕ Add Client'}",
            use_container_width=True
        )
        
        if submitted:
            # Convert date to string if needed
            if 'date_of_birth' in form_data and form_data['date_of_birth']:
                form_data['date_of_birth'] = str(form_data['date_of_birth'])
            
            return form_data
    
    return None

def render_header():
    """Render the application header"""
    st.markdown("""
    <div class="main-header">
        <h1 style='font-size:3em; margin:0;'>🎯 HRDISCCRM</h1>
        <p style='font-size:1.2em; margin:0.5rem 0 0 0; opacity:0.9;'>
            HR DISC Client Relationship Management • Real-time Google Sheets Integration
        </p>
    </div>
    """, unsafe_allow_html=True)

# ======= MAIN APPLICATION =======
def main():
    """Main application function"""
    try:
        # Render header
        render_header()
        
        # Setup authentication
        gc = setup_google_sheets_connection()
        
        # Store gc in session state for use in cached functions
        if gc:
            st.session_state['gc'] = gc
        
        # Sidebar controls
        with st.sidebar:
            st.markdown("---")
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
            
            # Mode selection
            st.header("🎛️ Application Mode")
            app_mode = st.selectbox(
                "Select Mode:",
                ["📊 View Clients", "➕ Add Client", "✏️ Edit Client", "📥 Export Data"],
                index=0
            )
            
            st.markdown("---")
            st.caption("HRDISCCRM v2.0 - Built with ❤️ using Streamlit")
        
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
        
        # Load data
        if 'df' not in st.session_state or st.session_state.df.empty:
            with st.spinner("🔄 Loading live client data..."):
                df, load_status = load_live_client_data(gc is not None)
                st.session_state.df = df
                st.session_state.load_status = load_status
                st.session_state.last_refresh = current_time
        else:
            df = st.session_state.df
            load_status = st.session_state.load_status
        
        # Display metrics
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
            client_count = safe_len(df)
            st.markdown(f"""
            <div class="metric-card">
                <h3>{client_count}</h3>
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
        
        # Display load status
        if load_status != "Success":
            st.markdown(f'<div class="warning-message">⚠️ Data Loading Issue: {load_status}</div>', unsafe_allow_html=True)
        
        # Main application logic based on mode
        if app_mode == "📊 View Clients":
            render_view_clients_mode(df)
        elif app_mode == "➕ Add Client":
            render_add_client_mode(gc)
        elif app_mode == "✏️ Edit Client":
            render_edit_client_mode(df, gc)
        elif app_mode == "📥 Export Data":
            render_export_mode(df)
        
    except Exception as e:
        st.markdown(f'<div class="error-message">❌ Critical Application Error: {e}</div>', unsafe_allow_html=True)
        st.info("Please refresh the page and try again. If the issue persists, check your data and authentication.")

def render_view_clients_mode(df: pd.DataFrame):
    """Render the view clients mode"""
    if df.empty:
        st.markdown('<div class="warning-message">📭 No client data found.</div>', unsafe_allow_html=True)
        return
    
    # Search and filter
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.subheader("🔍 Search & Filter Clients")
    
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
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter clients
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
    
    if filtered_df.empty:
        st.info("🔍 No clients found matching your search criteria.")
        return
    
    # Client selection and display
    st.subheader(f"👥 Client List ({len(filtered_df)} clients)")
    
    # Create client options
    client_options = []
    for idx, row in filtered_df.iterrows():
        try:
            full_name = safe_str(safe_get(row, 'full_name', 'Unknown'))
            email = safe_str(safe_get(row, 'email', 'No email'))
            company = safe_str(safe_get(row, 'company_id', 'No company'))
            completeness = get_client_completeness(row)
            
            # Status indicator
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
    
    if client_options:
        selected_option = st.selectbox(
            "Select a client to view their profile:",
            client_options,
            format_func=lambda x: x[0]
        )
        
        if selected_option:
            selected_display, selected_idx = selected_option
            
            if selected_idx is not None and selected_idx in filtered_df.index:
                render_client_profile(filtered_df.loc[selected_idx])

def render_client_profile(client_data: pd.Series):
    """Render individual client profile with enhanced display for large text"""
    try:
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
                    <h3 style='margin-top:0; color:#34495e;'>{category}</h3>
                """, unsafe_allow_html=True)
                
                for field in fields:
                    if field in CLIENT_FIELDS:
                        try:
                            field_label = field.replace('_', ' ').title()
                            field_value = safe_get(client_data, field)
                            
                            # Special handling for large text fields
                            if field in LARGE_TEXT_FIELDS and field_value and len(str(field_value)) > 50:
                                st.markdown(f"""
                                <div class="field-row">
                                    <div class="field-label">{field_label}:</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show full text in expandable section
                                with st.expander(f"View full {field_label.lower()}", expanded=False):
                                    st.markdown(f'<div class="large-text-value">{safe_str(field_value)}</div>', unsafe_allow_html=True)
                            else:
                                formatted_value = format_field_value(field_value, field)
                                st.markdown(f"""
                                <div class="field-row">
                                    <div class="field-label">{field_label}:</div>
                                    <div class="field-value">{formatted_value}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        except Exception as e:
                            st.warning(f"Error displaying field {field}: {e}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error displaying category {category}: {e}")
        
        # Profile actions
        st.markdown("---")
        st.subheader("🔧 Profile Actions")
        
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("📧 Send Email", key="send_email"):
                email_addr = safe_str(safe_get(client_data, 'email', ''))
                if email_addr and '@' in email_addr:
                    st.markdown(f'<div class="success-message">📧 Email client: <a href="mailto:{email_addr}" target="_blank">{email_addr}</a></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ No valid email address available</div>', unsafe_allow_html=True)
        
        with action_col2:
            if st.button("📞 Call Client", key="call_client"):
                phone = safe_str(safe_get(client_data, 'phone', ''))
                if phone and len(phone) >= 7:
                    st.markdown(f'<div class="success-message">📞 Call client: <a href="tel:{phone}">{phone}</a></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">❌ No valid phone number available</div>', unsafe_allow_html=True)
        
        with action_col3:
            if st.button("📝 Edit Profile", key="edit_profile"):
                st.info("📝 Switch to 'Edit Client' mode in the sidebar to edit this profile")
        
        # Export client data
        st.markdown("---")
        st.subheader("📥 Export Client Data")
        
        try:
            client_export_data = pd.DataFrame([client_data])
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                csv_data = export_to_csv_enhanced(client_export_data)
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

def render_add_client_mode(gc: Optional[gspread.Client]):
    """Render the add client mode"""
    if not gc:
        st.markdown('<div class="error-message">❌ Please authenticate with Google Sheets first</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<div class="edit-form">', unsafe_allow_html=True)
    
    form_data = render_client_form(mode="add")
    
    if form_data:
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        
        if missing_fields:
            st.markdown(f'<div class="error-message">❌ Please fill in required fields: {", ".join(missing_fields)}</div>', unsafe_allow_html=True)
        else:
            # Generate full_name if not provided
            if not form_data.get('full_name'):
                form_data['full_name'] = f"{form_data.get('first_name', '')} {form_data.get('last_name', '')}".strip()
            
            # Add client
            success, message = add_new_client(gc, form_data)
            
            if success:
                st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                # Clear cache to refresh data
                st.cache_data.clear()
                if 'df' in st.session_state:
                    del st.session_state['df']
                st.balloons()
            else:
                st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_edit_client_mode(df: pd.DataFrame, gc: Optional[gspread.Client]):
    """Render the edit client mode"""
    if not gc:
        st.markdown('<div class="error-message">❌ Please authenticate with Google Sheets first</div>', unsafe_allow_html=True)
        return
    
    if df.empty:
        st.markdown('<div class="warning-message">📭 No clients available to edit</div>', unsafe_allow_html=True)
        return
    
    # Client selection for editing
    st.subheader("✏️ Select Client to Edit")
    
    client_options = []
    for idx, row in df.iterrows():
        try:
            full_name = safe_str(safe_get(row, 'full_name', 'Unknown'))
            email = safe_str(safe_get(row, 'email', 'No email'))
            display_text = f"{full_name} ({email})"
            client_options.append((display_text, idx, row))
        except Exception:
            continue
    
    if client_options:
        selected_option = st.selectbox(
            "Choose a client to edit:",
            client_options,
            format_func=lambda x: x[0]
        )
        
        if selected_option:
            selected_display, selected_idx, selected_row = selected_option
            
            st.markdown('<div class="edit-form">', unsafe_allow_html=True)
            
            # Convert row to dict for form
            current_data = {field: safe_str(safe_get(selected_row, field)) for field in CLIENT_FIELDS}
            
            form_data = render_client_form(current_data, mode="edit")
            
            if form_data:
                # Update client
                success, message = update_client(gc, selected_idx, form_data)
                
                if success:
                    st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                    # Clear cache to refresh data
                    st.cache_data.clear()
                    if 'df' in st.session_state:
                        del st.session_state['df']
                    st.balloons()
                else:
                    st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

def render_export_mode(df: pd.DataFrame):
    """Render the export data mode"""
    if df.empty:
        st.markdown('<div class="warning-message">📭 No data available to export</div>', unsafe_allow_html=True)
        return
    
    st.subheader("📥 Export Client Data")
    
    # Export options
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        st.markdown("**📄 CSV Export (Enhanced)**")
        st.write("Optimized for large text fields and proper formatting")
        
        csv_data = export_to_csv_enhanced(df)
        st.download_button(
            label="📄 Download All Clients (CSV)",
            data=csv_data,
            file_name=f"hrdisccrm_clients_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    
    with export_col2:
        st.markdown("**🔗 JSON Export**")
        st.write("Structured data format for system integration")
        
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="🔗 Download All Clients (JSON)",
            data=json_data,
            file_name=f"hrdisccrm_clients_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime='application/json',
            use_container_width=True
        )
    
    # Data preview
    st.markdown("---")
    st.subheader("📊 Data Preview")
    
    # Show summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Records", len(df))
    
    with col2:
        filled_emails = df['email'].notna().sum() if 'email' in df.columns else 0
        st.metric("Valid Emails", filled_emails)
    
    with col3:
        avg_completeness = df.apply(lambda row: get_client_completeness(row), axis=1).mean()
        st.metric("Avg Completeness", f"{avg_completeness:.1f}%")
    
    # Show sample data
    st.markdown("**Sample Data (First 5 Records):**")
    st.dataframe(df.head(), use_container_width=True)

# ======= FOOTER =======
def render_footer():
    """Render application footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #7f8c8d; padding: 2rem;'>
        <p><strong>HRDISCCRM v2.0</strong></p>
        <p>🎯 HR DISC Client Relationship Management • 🔄 Real-time Google Sheets Integration</p>
        <p>Built with ❤️ using Streamlit + Google Sheets API</p>
    </div>
    """, unsafe_allow_html=True)

# ======= RUN APPLICATION =======
if __name__ == "__main__":
    main()
    render_footer()
