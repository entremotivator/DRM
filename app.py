import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from google.oauth2.service_account import Credentials
import time
import re
import io
import base64
from typing import Dict, List, Optional, Tuple, Any

# Import custom modules
from styles.theme import get_main_css, get_component_css, COLORS
from utils.formatters import (
    create_enhanced_csv, format_for_display, create_client_report_text,
    DISC_FIELDS, ADDRESS_FIELDS
)
from components.forms import render_add_client_form as render_add_form, render_edit_client_form

# ======= CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# Enhanced client fields with better organization
CLIENT_FIELDS = [
    "first_name", "last_name", "full_name", "email", "timezone",
    "address_line_1", "address_line_2", "city", "state", "postal_code", "country",
    "ip", "phone", "source", "date_of_birth", "company_id",
    "discprofile", "discsales", "disc_communiction", "leadership_style",
    "team_dynamics", "conflict_resolution", "customer_service_approach",
    "decision_making_style", "workplace_behavior", "hiring_and_recruitment",
    "_coaching_and_development"
]

# Enhanced field categories with better descriptions
FIELD_CATEGORIES = {
    "👤 Personal Information": {
        "fields": ["first_name", "last_name", "full_name", "email", "phone", 
                  "date_of_birth", "timezone", "ip", "source"],
        "description": "Basic personal and contact information"
    },
    "📍 Address & Location": {
        "fields": ["address_line_1", "address_line_2", "city", "state", 
                  "postal_code", "country"],
        "description": "Physical address and location details"
    },
    "🏢 Company & Business": {
        "fields": ["company_id"],
        "description": "Business and organizational information"
    },
    "🧠 DISC Assessment Profiles": {
        "fields": ["discprofile", "discsales", "disc_communiction", "leadership_style",
                  "team_dynamics", "conflict_resolution", "customer_service_approach",
                  "decision_making_style", "workplace_behavior"],
        "description": "Comprehensive DISC personality and behavioral assessments"
    },
    "📚 HR & Professional Development": {
        "fields": ["hiring_and_recruitment", "_coaching_and_development"],
        "description": "Human resources and professional development information"
    }
}

# ======= PAGE CONFIGURATION =======
st.set_page_config(
    page_title="Enhanced CRM Client Profiles", 
    layout="wide", 
    page_icon="👥",
    initial_sidebar_state="expanded"
)

# ======= APPLY CUSTOM THEME =======
st.markdown(get_main_css(), unsafe_allow_html=True)
st.markdown(get_component_css(), unsafe_allow_html=True)

# ======= ENHANCED UTILITY FUNCTIONS =======
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
    """Safely convert value to string with enhanced formatting"""
    try:
        if pd.isna(value):
            return default
        str_value = str(value).strip()
        return str_value if str_value else default
    except Exception:
        return default

def safe_len(obj: Any) -> int:
    """Safely get length of object"""
    try:
        return len(obj) if obj is not None else 0
    except Exception:
        return 0

# ======= ENHANCED HEADER =======
def render_header():
    """Render the enhanced application header"""
    try:
        current_time = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        st.markdown(f"""
        <div class="main-header fade-in">
            <h1 style='font-size:3.5em; margin:0; font-weight:700;'>👥 Enhanced CRM Client Profiles</h1>
            <p style='font-size:1.3em; margin:0.5rem 0 0 0; opacity:0.9; font-weight:500;'>
                🚀 Real-time Google Sheets Integration • 📊 Advanced Analytics • ✨ Modern Interface
            </p>
            <p style='font-size:1em; margin:0.5rem 0 0 0; opacity:0.8;'>
                Last updated: {current_time}
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying header: {e}")

# ======= ENHANCED SIDEBAR =======
def render_sidebar():
    """Render the enhanced sidebar with authentication and controls"""
    try:
        with st.sidebar:
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                        border-radius: 12px; margin-bottom: 1rem; border: 1px solid #90CAF9;'>
                <h2 style='margin: 0; color: #212121;'>🔧 Control Panel</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Authentication Section
            st.markdown("### 🔑 Authentication")
            auth_file = st.file_uploader(
                "Upload Service Account JSON", 
                type=["json"],
                help="Upload your Google Service Account JSON file to connect to Google Sheets"
            )
            
            gc = None
            if auth_file:
                try:
                    creds_dict = json.load(auth_file)
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=["https://www.googleapis.com/auth/spreadsheets"]
                    )
                    gc = gspread.authorize(creds)
                    st.success("✅ Successfully connected to Google Sheets!")
                    st.markdown(f"[📊 Open Sheet in New Tab]({SHEET_URL})")
                except Exception as e:
                    st.error(f"❌ Authentication Error: {str(e)[:100]}...")
            else:
                st.info("⬆️ Upload your Google Service Account JSON file to get started")
            
            st.markdown("---")
            
            # Live Updates Section
            st.markdown("### 🔄 Live Updates")
            auto_refresh = st.checkbox("Enable Auto-refresh", value=False)
            refresh_interval = 60
            
            if auto_refresh:
                refresh_interval = st.selectbox(
                    "Refresh Interval:",
                    [30, 60, 120, 300, 600],
                    index=1,
                    format_func=lambda x: f"{x} seconds ({x//60} min)" if x >= 60 else f"{x} seconds"
                )
            
            # Manual refresh button
            if st.button("🔄 Refresh Data Now", use_container_width=True):
                st.cache_data.clear()
                if 'df' in st.session_state:
                    del st.session_state['df']
                st.rerun()
            
            st.markdown("---")
            
            # Application Mode
            st.markdown("### 🎛️ Application Mode")
            app_mode = st.selectbox(
                "Select Mode:",
                ["View Profiles", "Add New Client", "Bulk Operations", "Analytics Dashboard"],
                help="Choose the application mode for different functionalities"
            )
            
            st.markdown("---")
            
            # Quick Stats (if data is available)
            if 'df' in st.session_state and not st.session_state.df.empty:
                st.markdown("### 📊 Quick Stats")
                df = st.session_state.df
                
                total_clients = len(df)
                complete_profiles = len(df[df.apply(lambda row: get_client_completeness(row) >= 80, axis=1)])
                avg_completeness = df.apply(lambda row: get_client_completeness(row), axis=1).mean()
                
                st.metric("Total Clients", total_clients)
                st.metric("Complete Profiles", f"{complete_profiles}/{total_clients}")
                st.metric("Avg Completeness", f"{avg_completeness:.1f}%")
            
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: #F3E5F5; 
                        border-radius: 12px; border: 1px solid #CE93D8;'>
                <p style='margin: 0; color: #212121; font-weight: 500;'>
                    Built with ❤️ using Streamlit<br>
                    <small>Enhanced CRM v2.0</small>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            return gc, auto_refresh, refresh_interval, app_mode
            
    except Exception as e:
        st.error(f"Error in sidebar: {e}")
        return None, False, 60, "View Profiles"

# ======= ENHANCED DATA LOADING =======
@st.cache_data(ttl=60)
def load_live_client_data():
    """Load live client data from Google Sheets with enhanced error handling"""
    if 'gc' not in st.session_state or not st.session_state.gc:
        return pd.DataFrame(columns=CLIENT_FIELDS), "No authentication"
    
    try:
        gc = st.session_state.gc
        sh = gc.open_by_key(SHEET_ID)
        
        # Enhanced worksheet detection
        worksheet_names = ["Clients", "Client Data", "Sheet1", "Main", "Data", "CRM"]
        worksheet = None
        
        # Get all available worksheets
        try:
            all_worksheets = sh.worksheets()
            available_names = [ws.title for ws in all_worksheets]
            st.sidebar.info(f"📋 Available sheets: {', '.join(available_names[:3])}{'...' if len(available_names) > 3 else ''}")
        except Exception:
            available_names = []
        
        # Try to find the right worksheet
        for name in worksheet_names:
            try:
                worksheet = sh.worksheet(name)
                st.sidebar.success(f"✅ Using sheet: **{name}**")
                break
            except gspread.exceptions.WorksheetNotFound:
                continue
        
        if not worksheet and all_worksheets:
            worksheet = all_worksheets[0]
            st.sidebar.warning(f"⚠️ Using first available sheet: **{worksheet.title}**")
        
        if not worksheet:
            return pd.DataFrame(columns=CLIENT_FIELDS), "No worksheets found"
        
        # Enhanced data loading with progress
        try:
            with st.spinner("📊 Loading client data..."):
                data = worksheet.get_all_values()
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error reading data: {e}"
        
        if not data:
            return pd.DataFrame(columns=CLIENT_FIELDS), "Sheet is empty"
        
        if len(data) < 2:
            return pd.DataFrame(columns=CLIENT_FIELDS), "No data rows found (only headers or empty)"
        
        # Enhanced DataFrame creation
        try:
            headers = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=headers)
            
            # Show column information
            st.sidebar.info(f"📊 Found {len(headers)} columns, {len(rows)} rows")
            
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error creating DataFrame: {e}"
        
        # Enhanced column handling
        missing_columns = []
        for col in CLIENT_FIELDS:
            if col not in df.columns:
                df[col] = ""
                missing_columns.append(col)
        
        if missing_columns:
            st.sidebar.warning(f"➕ Added {len(missing_columns)} missing columns")
        
        # Keep only the fields we want and clean data
        try:
            df = df[CLIENT_FIELDS].copy()
            df = clean_client_data(df)
            df = df.dropna(how='all')
            
            return df, "Success"
            
        except Exception as e:
            return pd.DataFrame(columns=CLIENT_FIELDS), f"Error processing data: {e}"
        
    except Exception as e:
        error_msg = f"Error loading data: {str(e)[:200]}"
        return pd.DataFrame(columns=CLIENT_FIELDS), error_msg

def clean_client_data(df: pd.DataFrame) -> pd.DataFrame:
    """Enhanced data cleaning with better formatting"""
    if df.empty:
        return df
    
    try:
        df_clean = df.copy()
        
        # Enhanced email cleaning
        if 'email' in df_clean.columns:
            try:
                df_clean['email'] = df_clean['email'].astype(str).str.lower().str.strip()
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
                df_clean.loc[~df_clean['email'].str.match(email_pattern, na=False), 'email'] = ''
            except Exception:
                pass
        
        # Enhanced phone cleaning
        if 'phone' in df_clean.columns:
            try:
                df_clean['phone'] = df_clean['phone'].astype(str).str.strip()
                # Remove non-phone entries
                df_clean.loc[df_clean['phone'].str.len() < 7, 'phone'] = ''
            except Exception:
                pass
        
        # Enhanced name formatting
        name_fields = ['first_name', 'last_name', 'full_name']
        for field in name_fields:
            if field in df_clean.columns:
                try:
                    df_clean[field] = df_clean[field].astype(str).str.title().str.strip()
                    df_clean.loc[df_clean[field].isin(['Nan', 'None', 'Null', '']), field] = ''
                except Exception:
                    pass
        
        # Enhanced date handling
        if 'date_of_birth' in df_clean.columns:
            try:
                df_clean['date_of_birth'] = pd.to_datetime(df_clean['date_of_birth'], errors='coerce')
            except Exception:
                pass
        
        # Clean DISC profile fields for better formatting
        disc_fields = ['discprofile', 'leadership_style', 'team_dynamics', 
                      'conflict_resolution', 'customer_service_approach',
                      'decision_making_style', 'workplace_behavior']
        
        for field in disc_fields:
            if field in df_clean.columns:
                try:
                    df_clean[field] = df_clean[field].astype(str).str.strip()
                    # Remove placeholder text
                    df_clean.loc[df_clean[field].isin(['Nan', 'None', 'Null', 'nan', 'none']), field] = ''
                except Exception:
                    pass
        
        return df_clean
        
    except Exception as e:
        st.error(f"Error cleaning data: {e}")
        return df

def get_client_completeness(client_data: pd.Series) -> float:
    """Calculate completeness percentage for a client with enhanced logic"""
    try:
        total_fields = len(CLIENT_FIELDS)
        filled_fields = 0
        
        for field in CLIENT_FIELDS:
            value = safe_str(safe_get(client_data, field, ""))
            if value and value.lower() not in ['', 'nan', 'none', 'null', 'n/a']:
                filled_fields += 1
        
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0
    except Exception:
        return 0

def format_field_value(value: Any, field_name: str) -> str:
    """Enhanced field value formatting with better display"""
    try:
        value_str = safe_str(value)
        
        if not value_str or value_str.lower() in ['nan', 'none', 'null', 'n/a']:
            return '<span class="empty-value">Not provided</span>'
        
        # Enhanced formatting for specific fields
        if field_name == 'email' and '@' in value_str:
            return f'<a href="mailto:{value_str}" target="_blank" style="color: {COLORS["primary_dark"]}; font-weight: 600;">{value_str}</a>'
        elif field_name == 'phone' and len(value_str) >= 7:
            return f'<a href="tel:{value_str}" style="color: {COLORS["accent_teal"]}; font-weight: 600;">{value_str}</a>'
        elif field_name == 'date_of_birth':
            try:
                date_obj = pd.to_datetime(value_str)
                return f'<span style="font-weight: 500;">{date_obj.strftime("%B %d, %Y")}</span>'
            except:
                return value_str
        elif 'address' in field_name or field_name in ['city', 'state', 'country']:
            return f'<span style="font-weight: 500;">{value_str.title()}</span>'
        elif field_name in ['discprofile', 'leadership_style', 'team_dynamics', 
                           'conflict_resolution', 'customer_service_approach',
                           'decision_making_style', 'workplace_behavior']:
            # Format long DISC text with better display
            if len(value_str) > 100:
                truncated = value_str[:100] + "..."
                return f'<span style="font-weight: 400; line-height: 1.4;" title="{value_str}">{truncated}</span>'
            else:
                return f'<span style="font-weight: 400; line-height: 1.4;">{value_str}</span>'
        else:
            return f'<span style="font-weight: 500;">{value_str}</span>'
    except Exception:
        return '<span class="empty-value">Error displaying value</span>'

# ======= ENHANCED METRICS DISPLAY =======
def render_metrics(df: pd.DataFrame, gc: Any):
    """Render enhanced metrics with better visualization"""
    try:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            status = "🟢 Connected" if gc else "🔴 Disconnected"
            status_color = COLORS['accent_green'] if gc else COLORS['accent_red']
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {status_color};">{status}</h3>
                <p>Google Sheets</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            client_count = safe_len(df)
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {COLORS['primary_dark']};">{client_count:,}</h3>
                <p>Total Clients</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if not df.empty:
                complete_profiles = len(df[df.apply(lambda row: get_client_completeness(row) >= 80, axis=1)])
            else:
                complete_profiles = 0
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {COLORS['accent_green']};">{complete_profiles}</h3>
                <p>Complete Profiles</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            if not df.empty:
                avg_completeness = df.apply(lambda row: get_client_completeness(row), axis=1).mean()
            else:
                avg_completeness = 0
            completeness_color = COLORS['accent_green'] if avg_completeness >= 70 else COLORS['accent_orange'] if avg_completeness >= 50 else COLORS['accent_red']
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {completeness_color};">{avg_completeness:.1f}%</h3>
                <p>Avg Completeness</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            last_update = datetime.datetime.now().strftime("%H:%M:%S")
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="color: {COLORS['accent_teal']};">{last_update}</h3>
                <p>Last Updated</p>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error displaying metrics: {e}")

# ======= MAIN APPLICATION =======
def main():
    """Main application function with enhanced features"""
    try:
        # Render header
        render_header()
        
        # Render sidebar and get controls
        gc, auto_refresh, refresh_interval, app_mode = render_sidebar()
        
        # Store gc in session state for caching
        st.session_state.gc = gc
        
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
        
        # Load data if needed
        if 'df' not in st.session_state or st.session_state.df.empty or gc:
            df, load_status = load_live_client_data()
            st.session_state.df = df
            st.session_state.load_status = load_status
            st.session_state.last_refresh = current_time
        else:
            df = st.session_state.df
            load_status = st.session_state.load_status
        
        # Render metrics
        render_metrics(df, gc)
        
        # Display load status
        if load_status != "Success":
            st.markdown(f"""
            <div class="warning-container">
                <strong>⚠️ Data Loading Issue:</strong> {load_status}
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced debug information
        with st.expander("🔍 Debug Information & System Status", expanded=False):
            debug_col1, debug_col2 = st.columns(2)
            
            with debug_col1:
                st.write("**System Status:**")
                st.write(f"- Load Status: {load_status}")
                st.write(f"- DataFrame Shape: {df.shape if not df.empty else 'Empty'}")
                st.write(f"- Authentication: {'✅ Connected' if gc else '❌ Not Connected'}")
                st.write(f"- Auto Refresh: {'✅ Enabled' if auto_refresh else '❌ Disabled'}")
                st.write(f"- App Mode: {app_mode}")
            
            with debug_col2:
                if not df.empty:
                    st.write("**Data Sample:**")
                    st.dataframe(df.head(3), use_container_width=True)
                else:
                    st.write("**No data available**")
        
        # Main application logic based on mode
        if app_mode == "View Profiles":
            render_profile_viewer(df)
        elif app_mode == "Add New Client":
            render_add_client_form()
        elif app_mode == "Bulk Operations":
            render_bulk_operations(df)
        elif app_mode == "Analytics Dashboard":
            render_analytics_dashboard(df)
        
        # Enhanced footer
        render_footer()
        
    except Exception as e:
        st.markdown(f"""
        <div class="error-container">
            <strong>❌ Critical Application Error:</strong> {str(e)}
            <br><small>Please refresh the page and try again. If the issue persists, check your data and authentication.</small>
        </div>
        """, unsafe_allow_html=True)

def render_profile_viewer(df: pd.DataFrame):
    """Render the enhanced profile viewer"""
    if df.empty:
        render_empty_state()
        return
    
    try:
        # Enhanced search and filter section
        st.markdown('<div class="search-container slide-in">', unsafe_allow_html=True)
        st.markdown("### 🔍 Find & Filter Clients")
        
        search_col1, search_col2, search_col3 = st.columns([2, 1, 1])
        
        with search_col1:
            search_term = st.text_input(
                "🔎 Search clients:",
                placeholder="Search by name, email, company, or any field...",
                help="Search across all client fields with instant results"
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
        
        with search_col3:
            completeness_filter = st.selectbox(
                "📈 Completeness:",
                ["All", "Complete (80%+)", "Partial (50-79%)", "Incomplete (<50%)"]
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Apply filters
        filtered_df = apply_filters(df, search_term, sort_by, completeness_filter)
        
        # Display results
        if filtered_df.empty:
            st.markdown("""
            <div class="info-container">
                <strong>🔍 No clients found</strong> matching your search criteria.
                <br><small>Try adjusting your search terms or filters.</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            render_client_list(filtered_df)
            
    except Exception as e:
        st.error(f"Error in profile viewer: {e}")

def apply_filters(df: pd.DataFrame, search_term: str, sort_by: str, completeness_filter: str) -> pd.DataFrame:
    """Apply search and filter criteria to the dataframe"""
    try:
        filtered_df = df.copy()
        
        # Apply search filter
        if search_term:
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = df[mask]
        
        # Apply completeness filter
        if completeness_filter != "All":
            if completeness_filter == "Complete (80%+)":
                mask = filtered_df.apply(lambda row: get_client_completeness(row) >= 80, axis=1)
            elif completeness_filter == "Partial (50-79%)":
                mask = filtered_df.apply(lambda row: 50 <= get_client_completeness(row) < 80, axis=1)
            elif completeness_filter == "Incomplete (<50%)":
                mask = filtered_df.apply(lambda row: get_client_completeness(row) < 50, axis=1)
            
            filtered_df = filtered_df[mask]
        
        # Apply sorting
        if sort_by and sort_by in filtered_df.columns:
            filtered_df = filtered_df.sort_values(sort_by)
        
        return filtered_df
        
    except Exception as e:
        st.warning(f"Filter error: {e}")
        return df

def render_client_list(filtered_df: pd.DataFrame):
    """Render the enhanced client list with selection"""
    try:
        st.markdown(f"### 👥 Client List ({len(filtered_df):,} clients)")
        
        # Create enhanced client options
        client_options = []
        for idx, row in filtered_df.iterrows():
            try:
                full_name = safe_str(safe_get(row, 'full_name', 'Unknown'))
                email = safe_str(safe_get(row, 'email', 'No email'))
                company = safe_str(safe_get(row, 'company_id', 'No company'))
                completeness = get_client_completeness(row)
                
                # Enhanced status indicator
                if completeness >= 80:
                    status = "🟢"
                    status_text = "Complete"
                elif completeness >= 50:
                    status = "🟡"
                    status_text = "Partial"
                else:
                    status = "🔴"
                    status_text = "Incomplete"
                
                display_text = f"{status} {full_name} • {email} • {company} • {status_text} ({completeness:.0f}%)"
                client_options.append((display_text, idx))
            except Exception as e:
                st.warning(f"Error processing client at index {idx}: {e}")
                continue
        
        # Client selection with enhanced display
        if client_options:
            selected_option = st.selectbox(
                "Select a client to view their detailed profile:",
                client_options,
                format_func=lambda x: x[0],
                help="Choose a client from the list to view their complete profile information"
            )
            
            if selected_option:
                selected_display, selected_idx = selected_option
                
                if selected_idx is not None and selected_idx in filtered_df.index:
                    render_client_profile(filtered_df.loc[selected_idx])
                else:
                    st.error("Selected client not found in data")
        else:
            st.warning("No valid client options available")
            
    except Exception as e:
        st.error(f"Error creating client list: {e}")

def render_client_profile(client_data: pd.Series):
    """Render enhanced individual client profile"""
    try:
        # Enhanced profile header
        full_name = safe_str(safe_get(client_data, 'full_name', 'Unknown Client'))
        email = safe_str(safe_get(client_data, 'email', 'No email provided'))
        company = safe_str(safe_get(client_data, 'company_id', 'No company'))
        completeness = get_client_completeness(client_data)
        
        # Determine completeness color
        if completeness >= 80:
            completeness_color = COLORS['accent_green']
            completeness_icon = "🟢"
        elif completeness >= 50:
            completeness_color = COLORS['accent_orange']
            completeness_icon = "🟡"
        else:
            completeness_color = COLORS['accent_red']
            completeness_icon = "🔴"
        
        st.markdown(f"""
        <div class="profile-header fade-in">
            <h1 style='margin:0; font-size:3em; font-weight:700;'>{full_name}</h1>
            <p style='margin:0.5rem 0 0 0; font-size:1.3em; opacity:0.9; font-weight:500;'>{email}</p>
            <p style='margin:0.3rem 0 0 0; font-size:1.1em; opacity:0.8; font-weight:500;'>{company}</p>
            <p style='margin:1rem 0 0 0; font-size:1.1em; color: {completeness_color}; font-weight:600;'>
                {completeness_icon} Profile Completeness: {completeness:.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced field display by category
        for category, category_info in FIELD_CATEGORIES.items():
            fields = category_info["fields"]
            description = category_info["description"]
            
            try:
                st.markdown(f"""
                <div class="field-section slide-in">
                    <h3 style='margin-top:0; color:{COLORS["text_primary"]}; font-weight:600;'>{category}</h3>
                    <p style='margin-bottom:1.5rem; color:{COLORS["text_muted"]}; font-style:italic;'>{description}</p>
                """, unsafe_allow_html=True)
                
                # Create field rows with enhanced formatting
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
        
        # Enhanced profile actions
        render_profile_actions(client_data, full_name)
        
    except Exception as e:
        st.error(f"Error displaying client profile: {e}")

def render_profile_actions(client_data: pd.Series, full_name: str):
    """Render enhanced profile action buttons"""
    try:
        st.markdown("---")
        st.markdown("### 🔧 Profile Actions")
        
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button("📧 Send Email", key="send_email", use_container_width=True):
                email_addr = safe_str(safe_get(client_data, 'email', ''))
                if email_addr and '@' in email_addr:
                    st.markdown(f"""
                    <div class="success-container">
                        <strong>📧 Email Action:</strong> Ready to email {email_addr}
                        <br><a href="mailto:{email_addr}" target="_blank" style="color: {COLORS['primary_dark']}; font-weight: 600;">Open Email Client</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-container">
                        <strong>❌ No valid email address available</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        with action_col2:
            if st.button("📞 Call Client", key="call_client", use_container_width=True):
                phone = safe_str(safe_get(client_data, 'phone', ''))
                if phone and len(phone) >= 7:
                    st.markdown(f"""
                    <div class="success-container">
                        <strong>📞 Call Action:</strong> Ready to call {phone}
                        <br><a href="tel:{phone}" style="color: {COLORS['accent_teal']}; font-weight: 600;">Call Now</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-container">
                        <strong>❌ No valid phone number available</strong>
                    </div>
                    """, unsafe_allow_html=True)
        
        with action_col3:
            if st.button("📝 Edit Profile", key="edit_profile", use_container_width=True):
                st.markdown("""
                <div class="info-container">
                    <strong>📝 Edit functionality</strong> - Coming in next update!
                    <br><small>Switch to "Add New Client" mode to see the form interface.</small>
                </div>
                """, unsafe_allow_html=True)
        
        with action_col4:
            if st.button("📊 View Analytics", key="view_analytics", use_container_width=True):
                st.markdown("""
                <div class="info-container">
                    <strong>📊 Analytics view</strong> - Switch to "Analytics Dashboard" mode
                    <br><small>View comprehensive client analytics and insights.</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced export section
        st.markdown("---")
        st.markdown("### 📥 Export Client Data")
        
        try:
            client_export_data = pd.DataFrame([client_data])
            
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                csv_data = create_enhanced_csv(client_export_data)
                st.download_button(
                    label="📄 Download Enhanced CSV",
                    data=csv_data,
                    file_name=f"{full_name.replace(' ', '_')}_profile_enhanced.csv",
                    mime='text/csv',
                    use_container_width=True,
                    help="Download with improved formatting for long text fields"
                )
            
            with export_col2:
                json_data = client_export_data.to_json(orient='records', indent=2)
                st.download_button(
                    label="🔗 Download JSON",
                    data=json_data,
                    file_name=f"{full_name.replace(' ', '_')}_profile.json",
                    mime='application/json',
                    use_container_width=True
                )
            
            with export_col3:
                # Create a formatted text report
                report_data = create_client_report(client_data)
                st.download_button(
                    label="📋 Download Report",
                    data=report_data,
                    file_name=f"{full_name.replace(' ', '_')}_report.txt",
                    mime='text/plain',
                    use_container_width=True,
                    help="Download formatted text report"
                )
        except Exception as e:
            st.error(f"Export error: {e}")
            
    except Exception as e:
        st.error(f"Error in profile actions: {e}")

def create_client_report(client_data: pd.Series) -> str:
    """Create a formatted text report for a client"""
    try:
        full_name = safe_str(safe_get(client_data, 'full_name', 'Unknown Client'))
        report_lines = [
            f"CLIENT PROFILE REPORT",
            f"=" * 50,
            f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            f"",
            f"CLIENT: {full_name}",
            f"COMPLETENESS: {get_client_completeness(client_data):.1f}%",
            f"",
        ]
        
        for category, category_info in FIELD_CATEGORIES.items():
            fields = category_info["fields"]
            description = category_info["description"]
            
            report_lines.append(f"{category}")
            report_lines.append(f"{description}")
            report_lines.append("-" * 40)
            
            for field in fields:
                if field in CLIENT_FIELDS:
                    field_label = field.replace('_', ' ').title()
                    value = safe_str(safe_get(client_data, field, 'Not provided'))
                    report_lines.append(f"{field_label}: {value}")
            
            report_lines.append("")
        
        return "\\n".join(report_lines)
    except Exception:
        return "Error generating report"

def render_add_client_form():
    """Render the add new client form using the forms module"""
    gc = st.session_state.get('gc', None)
    render_add_form(gc)

def render_bulk_operations(df: pd.DataFrame):
    """Render bulk operations interface (placeholder for now)"""
    st.markdown("""
    <div class="info-container">
        <h3>🔄 Bulk Operations - Coming Soon!</h3>
        <p>This feature will allow you to perform operations on multiple clients at once.</p>
        <p><strong>Planned features:</strong></p>
        <ul>
            <li>📤 Bulk export with custom formatting</li>
            <li>📧 Mass email campaigns</li>
            <li>🏷️ Batch tagging and categorization</li>
            <li>📊 Bulk data analysis and reporting</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_analytics_dashboard(df: pd.DataFrame):
    """Render analytics dashboard (placeholder for now)"""
    st.markdown("""
    <div class="info-container">
        <h3>📊 Analytics Dashboard - Coming Soon!</h3>
        <p>This feature will provide comprehensive analytics and insights about your client data.</p>
        <p><strong>Planned features:</strong></p>
        <ul>
            <li>📈 Client completeness trends</li>
            <li>🧠 DISC profile distribution charts</li>
            <li>🌍 Geographic client mapping</li>
            <li>📅 Client acquisition timeline</li>
            <li>🎯 Performance metrics and KPIs</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def render_empty_state():
    """Render empty state when no data is available"""
    st.markdown("""
    <div class="warning-container">
        <h3>📭 No client data found</h3>
        <p>It looks like there's no client data available. This could be due to several reasons:</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔧 Troubleshooting Steps:")
    
    troubleshoot_col1, troubleshoot_col2 = st.columns(2)
    
    with troubleshoot_col1:
        st.markdown("""
        **Authentication & Access:**
        1. 🔑 Upload your Google Service Account JSON file
        2. 🔐 Ensure the service account has access to your sheet
        3. 📊 Verify the Sheet ID is correct
        4. 🌐 Check your internet connection
        """)
    
    with troubleshoot_col2:
        st.markdown("""
        **Data Structure:**
        1. 📋 Ensure your sheet has headers in the first row
        2. 📝 Verify there are data rows below the headers
        3. 🏷️ Try naming your sheet 'Clients' or 'Client Data'
        4. 🔍 Check for any data formatting issues
        """)
    
    st.markdown("### 📋 Expected Column Names:")
    
    # Display expected columns in a nice format
    cols = st.columns(4)
    for i, field in enumerate(CLIENT_FIELDS):
        with cols[i % 4]:
            st.code(field)

def render_footer():
    """Render enhanced footer"""
    try:
        st.markdown("---")
        st.markdown(f"""
        <div class="footer fade-in">
            <h4 style='margin-top:0; color:{COLORS["text_primary"]};'>Enhanced CRM Client Profiles</h4>
            <p style='margin:0.5rem 0; color:{COLORS["text_secondary"]};'>
                🚀 Real-time Google Sheets Integration • 📊 Advanced Analytics • ✨ Modern Interface
            </p>
            <p style='margin:0.5rem 0; color:{COLORS["text_muted"]}; font-size:0.9rem;'>
                Built with ❤️ using Streamlit + Google Sheets API • Enhanced CRM v2.0
            </p>
            <p style='margin:0; color:{COLORS["text_muted"]}; font-size:0.8rem;'>
                © 2024 Enhanced CRM Application • Powered by Modern Web Technologies
            </p>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.write("Enhanced CRM Client Profiles - Built with Streamlit")

# ======= RUN APPLICATION =======
if __name__ == "__main__":
    main()
