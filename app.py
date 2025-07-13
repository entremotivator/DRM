import streamlit as st
import pandas as pd
import datetime
import gspread
import json
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import numpy as np
from collections import Counter
import re

# ======= ENHANCED CONFIGURATION =======
SHEET_ID = "188i0tHyaEH_0hkSXfdMXoP1c3quEp54EAyuqmMUgHN0"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# Enhanced tabs configuration with descriptions
tabs_config = {
    "Basic Info": {
        "columns": [
            "first_name", "last_name", "full_name", "email", "phone", "company_id",
            "industry", "position", "company_size", "website", "source", "assessment_date"
        ],
        "description": "Core client information and contact details",
        "icon": "👤"
    },
    "Contact Info": {
        "columns": ["full_name", "address_line_1", "city", "state", "postal_code", "country"],
        "description": "Physical addresses and location data",
        "icon": "📍"
    },
    "DISC General Profile": {
        "columns": ["full_name", "discprofile"],
        "description": "General DISC personality assessments",
        "icon": "🧠"
    },
    "DISC Sales Profile": {
        "columns": ["full_name", "discsales"],
        "description": "Sales-focused DISC analysis",
        "icon": "💼"
    },
    "DISC Communication Style": {
        "columns": ["full_name", "disc_communiction"],
        "description": "Communication preferences and styles",
        "icon": "💬"
    },
    "DISC Leadership Style": {
        "columns": ["full_name", "leadership_style"],
        "description": "Leadership approach and management style",
        "icon": "👑"
    },
    "DISC Team Dynamics": {
        "columns": ["full_name", "team_dynamics"],
        "description": "Team collaboration and interaction patterns",
        "icon": "👥"
    },
    "DISC Conflict Resolution": {
        "columns": ["full_name", "conflict_resolution"],
        "description": "Conflict handling and resolution approaches",
        "icon": "⚖️"
    },
    "DISC Customer Service Approach": {
        "columns": ["full_name", "customer_service_approach"],
        "description": "Customer service and client interaction styles",
        "icon": "🤝"
    },
    "DISC Decision-Making Style": {
        "columns": ["full_name", "decision_making_style"],
        "description": "Decision-making processes and preferences",
        "icon": "🎯"
    },
    "DISC Workplace Behavior": {
        "columns": ["full_name", "workplace_behavior"],
        "description": "Professional behavior and work environment preferences",
        "icon": "🏢"
    },
    "HR & Coaching": {
        "columns": [
            "full_name", "hiring_and_recruitment", "_coaching_and_development",
            "career_goals", "stress_management", "learning_style"
        ],
        "description": "Human resources and professional development data",
        "icon": "📚"
    }
}

# ======= PAGE CONFIGURATION =======
st.set_page_config(
    page_title="Enhanced CRM Manager", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ======= CUSTOM CSS STYLING =======
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .tab-description {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .data-quality-good { color: #4CAF50; font-weight: bold; }
    .data-quality-warning { color: #FF9800; font-weight: bold; }
    .data-quality-error { color: #f44336; font-weight: bold; }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ======= HEADER =======
st.markdown("""
<div class="main-header">
    <h1 style='font-size:3em; margin:0;'>📊 Enhanced CRM Client Profiles Manager</h1>
    <p style='font-size:1.2em; margin:0.5rem 0 0 0; opacity:0.9;'>
        Advanced Analytics • Data Insights • Professional Management
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
            st.success("✅ Authentication Successful!")
            st.markdown(f"[📊 Open Google Sheet]({SHEET_URL})")
        except Exception as e:
            st.error(f"❌ Auth Error: {str(e)[:100]}...")
    else:
        st.info("⬆️ Upload your Google Service Account JSON")
    
    st.markdown("---")
    
    # ======= NAVIGATION =======
    st.header("📋 Navigation")
    view_mode = st.radio(
        "Select View:",
        ["📊 Dashboard", "📋 Data Management", "📈 Analytics", "⚙️ Settings"],
        index=0
    )
    
    if view_mode == "📋 Data Management":
        selected_tab = st.selectbox(
            "Select CRM Section:",
            list(tabs_config.keys()),
            format_func=lambda x: f"{tabs_config[x]['icon']} {x}"
        )
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit")

# ======= UTILITY FUNCTIONS =======
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_gsheet_data(tab_name):
    """Load data from Google Sheets with caching"""
    expected_columns = tabs_config[tab_name]["columns"]
    
    if not gc:
        return pd.DataFrame(columns=expected_columns)
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        try:
            worksheet = sh.worksheet(tab_name)
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
        
        # Clean and validate data
        df = clean_dataframe(df)
        
        return df
    except Exception as e:
        st.error(f"❌ Could not load Google Sheet: {e}")
        return pd.DataFrame(columns=expected_columns)

def clean_dataframe(df):
    """Clean and standardize dataframe data"""
    if df.empty:
        return df
        
    df_clean = df.copy()
    
    # Clean email addresses
    if 'email' in df_clean.columns:
        df_clean['email'] = df_clean['email'].astype(str).str.lower().str.strip()
    
    # Clean phone numbers
    if 'phone' in df_clean.columns:
        df_clean['phone'] = df_clean['phone'].astype(str).str.replace(r'[^\d+\-$$$$\s]', '', regex=True)
    
    # Standardize names
    name_columns = ['first_name', 'last_name', 'full_name']
    for col in name_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.title().str.strip()
    
    # Handle dates
    if 'assessment_date' in df_clean.columns:
        df_clean['assessment_date'] = pd.to_datetime(df_clean['assessment_date'], errors='coerce')
    
    return df_clean

def validate_data_quality(df):
    """Analyze data quality and return metrics"""
    if df.empty:
        return {
            "overall_score": 0, 
            "issues": [], 
            "completeness": 0,
            "total_records": 0,
            "empty_cells": 0
        }
    
    issues = []
    total_cells = df.size
    
    # Count empty cells more safely
    empty_cells = 0
    try:
        empty_cells += df.isnull().sum().sum()
        empty_cells += (df.astype(str) == "").sum().sum()
        empty_cells += (df.astype(str) == "nan").sum().sum()
    except Exception:
        # Fallback method
        for col in df.columns:
            try:
                empty_cells += df[col].isnull().sum()
                empty_cells += (df[col].astype(str) == "").sum()
            except Exception:
                continue
    
    completeness = ((total_cells - empty_cells) / total_cells) * 100 if total_cells > 0 else 0
    
    # Check for duplicate emails
    if 'email' in df.columns:
        try:
            email_series = df['email'].dropna()
            email_series = email_series[email_series.astype(str) != ""]
            email_duplicates = email_series.duplicated().sum()
            if email_duplicates > 0:
                issues.append(f"🔄 {email_duplicates} duplicate email addresses")
        except Exception:
            pass
    
    # Check for invalid emails
    if 'email' in df.columns:
        try:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            valid_emails = df['email'].dropna()
            valid_emails = valid_emails[valid_emails.astype(str) != ""]
            if len(valid_emails) > 0:
                invalid_emails = valid_emails.apply(
                    lambda x: not re.match(email_pattern, str(x)) if pd.notna(x) else False
                ).sum()
                if invalid_emails > 0:
                    issues.append(f"📧 {invalid_emails} invalid email formats")
        except Exception:
            pass
    
    # Check for missing critical fields
    critical_fields = ['full_name', 'email']
    for field in critical_fields:
        if field in df.columns:
            try:
                missing = df[field].isnull().sum() + (df[field].astype(str) == "").sum()
                if missing > 0:
                    issues.append(f"❗ {missing} missing {field} entries")
            except Exception:
                pass
    
    # Calculate overall score
    overall_score = max(0, completeness - len(issues) * 5)
    
    return {
        "overall_score": overall_score,
        "issues": issues,
        "completeness": completeness,
        "total_records": len(df),
        "empty_cells": empty_cells
    }

def create_summary_metrics(all_data):
    """Create summary metrics across all tabs"""
    total_records = 0
    unique_clients = set()
    industries = {}
    recent_assessments = 0
    
    try:
        total_records = sum(len(df) for df in all_data.values() if not df.empty)
        
        # Get unique clients across all tabs
        for df in all_data.values():
            if not df.empty and 'full_name' in df.columns:
                try:
                    valid_names = df['full_name'].dropna()
                    valid_names = valid_names[valid_names.astype(str) != ""]
                    unique_clients.update(valid_names.unique())
                except Exception:
                    continue
        
        # Industry distribution from Basic Info
        if 'Basic Info' in all_data and not all_data['Basic Info'].empty:
            try:
                basic_df = all_data['Basic Info']
                if 'industry' in basic_df.columns:
                    industry_series = basic_df['industry'].dropna()
                    industry_series = industry_series[industry_series.astype(str) != ""]
                    industries = industry_series.value_counts().to_dict()
            except Exception:
                pass
        
        # Recent assessments
        if 'Basic Info' in all_data and not all_data['Basic Info'].empty:
            try:
                df = all_data['Basic Info']
                if 'assessment_date' in df.columns:
                    recent_date = datetime.datetime.now() - datetime.timedelta(days=30)
                    date_series = pd.to_datetime(df['assessment_date'], errors='coerce')
                    recent_assessments = len(date_series[date_series > recent_date])
            except Exception:
                pass
                
    except Exception as e:
        st.error(f"Error creating summary metrics: {e}")
    
    return {
        "total_records": total_records,
        "unique_clients": len(unique_clients),
        "industries": industries,
        "recent_assessments": recent_assessments
    }

# ======= SAFE DATA ACCESS FUNCTIONS =======
def safe_get(dictionary, key, default=0):
    """Safely get a value from dictionary with default"""
    try:
        return dictionary.get(key, default)
    except Exception:
        return default

def safe_len(obj):
    """Safely get length of object"""
    try:
        return len(obj) if obj is not None else 0
    except Exception:
        return 0

# ======= MAIN APPLICATION LOGIC =======

try:
    if view_mode == "📊 Dashboard":
        st.header("📊 CRM Dashboard")
        
        # Load all data for dashboard
        all_data = {}
        with st.spinner("Loading dashboard data..."):
            for tab_name in tabs_config.keys():
                try:
                    all_data[tab_name] = load_gsheet_data(tab_name)
                except Exception as e:
                    st.warning(f"Could not load {tab_name}: {e}")
                    all_data[tab_name] = pd.DataFrame()
        
        # Summary metrics
        metrics = create_summary_metrics(all_data)
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📊 Total Records",
                value=safe_get(metrics, "total_records", 0),
                delta=f"Across {len(tabs_config)} sections"
            )
        
        with col2:
            st.metric(
                label="👥 Unique Clients",
                value=safe_get(metrics, "unique_clients", 0),
                delta="Individual profiles"
            )
        
        with col3:
            industries_count = safe_len(safe_get(metrics, "industries", {}))
            st.metric(
                label="🏭 Industries",
                value=industries_count,
                delta="Different sectors"
            )
        
        with col4:
            st.metric(
                label="📅 Recent Assessments",
                value=safe_get(metrics, "recent_assessments", 0),
                delta="Last 30 days"
            )
        
        # Data distribution charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Records by Section")
            section_data = {name: len(df) for name, df in all_data.items() if not df.empty}
            if section_data:
                try:
                    fig = px.bar(
                        x=list(section_data.keys()),
                        y=list(section_data.values()),
                        title="Records Distribution Across Sections",
                        color=list(section_data.values()),
                        color_continuous_scale="Greens"
                    )
                    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating chart: {e}")
            else:
                st.info("No data available for chart")
        
        with col2:
            st.subheader("🏭 Industry Distribution")
            industries = safe_get(metrics, "industries", {})
            if industries:
                try:
                    fig = px.pie(
                        values=list(industries.values()),
                        names=list(industries.keys()),
                        title="Client Distribution by Industry"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating pie chart: {e}")
            else:
                st.info("No industry data available")
        
        # Data quality overview
        st.subheader("🔍 Data Quality Overview")
        
        # Create columns dynamically based on available data
        available_tabs = [name for name, df in all_data.items() if not df.empty]
        if available_tabs:
            num_cols = min(4, len(available_tabs))  # Max 4 columns
            quality_cols = st.columns(num_cols)
            
            for idx, tab_name in enumerate(available_tabs):
                col_idx = idx % num_cols
                with quality_cols[col_idx]:
                    try:
                        df = all_data[tab_name]
                        quality = validate_data_quality(df)
                        score = safe_get(quality, "overall_score", 0)
                        
                        if score >= 80:
                            color = "data-quality-good"
                            icon = "✅"
                        elif score >= 60:
                            color = "data-quality-warning"
                            icon = "⚠️"
                        else:
                            color = "data-quality-error"
                            icon = "❌"
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>{icon} {tab_name}</h4>
                            <p class="{color}">Quality Score: {score:.1f}%</p>
                            <p>Records: {safe_get(quality, 'total_records', 0)}</p>
                            <p>Completeness: {safe_get(quality, 'completeness', 0):.1f}%</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error processing {tab_name}: {e}")
        else:
            st.info("No data available for quality analysis")

    elif view_mode == "📋 Data Management":
        # Get tab configuration
        tab_config = tabs_config[selected_tab]
        expected_columns = tab_config["columns"]
        
        # Display tab information
        st.markdown(f"""
        <div class="tab-description">
            <h3>{tab_config['icon']} {selected_tab}</h3>
            <p>{tab_config['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Load data
        if "df" not in st.session_state or st.session_state.get("last_tab") != selected_tab:
            with st.spinner(f"Loading {selected_tab} data..."):
                try:
                    st.session_state.df = load_gsheet_data(selected_tab)
                    st.session_state.last_tab = selected_tab
                except Exception as e:
                    st.error(f"Error loading data: {e}")
                    st.session_state.df = pd.DataFrame(columns=expected_columns)
        
        df = st.session_state.df
        
        # Data quality check
        quality = validate_data_quality(df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Records", safe_get(quality, "total_records", 0))
        with col2:
            st.metric("✅ Data Quality", f"{safe_get(quality, 'overall_score', 0):.1f}%")
        with col3:
            st.metric("📈 Completeness", f"{safe_get(quality, 'completeness', 0):.1f}%")
        
        # Display data quality issues
        issues = safe_get(quality, "issues", [])
        if issues:
            with st.expander("⚠️ Data Quality Issues", expanded=False):
                for issue in issues:
                    st.warning(issue)
        
        # ======= ENHANCED FILTERING =======
        st.subheader("🔍 Advanced Filtering")
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            # Text search
            search_term = st.text_input("🔎 Search all fields:", placeholder="Enter search term...")
        
        with filter_col2:
            # Column filter
            if not df.empty:
                filter_column = st.selectbox("📋 Filter by column:", ["All"] + expected_columns)
            else:
                filter_column = "All"
        
        with filter_col3:
            # Date range filter (if applicable)
            date_filter = False
            if 'assessment_date' in expected_columns and not df.empty:
                date_filter = st.checkbox("📅 Filter by date range")
                if date_filter:
                    start_date = st.date_input("Start date", datetime.date.today() - datetime.timedelta(days=365))
                    end_date = st.date_input("End date", datetime.date.today())
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term and not df.empty:
            try:
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                filtered_df = df[mask]
            except Exception as e:
                st.warning(f"Search error: {e}")
        
        if filter_column != "All" and not df.empty:
            try:
                unique_values = df[filter_column].dropna().unique()
                unique_values = [str(val) for val in unique_values if str(val) != ""]
                if unique_values:
                    selected_values = st.multiselect(f"Select {filter_column} values:", unique_values)
                    if selected_values:
                        filtered_df = filtered_df[filtered_df[filter_column].astype(str).isin(selected_values)]
            except Exception as e:
                st.warning(f"Filter error: {e}")
        
        # ======= CSV UPLOAD AND MERGE =======
        st.subheader("📤 Data Import")
        uploaded_file = st.file_uploader(f"Upload {selected_tab} CSV to merge:", type=["csv"])
        
        if uploaded_file:
            try:
                new_df = pd.read_csv(uploaded_file)
                
                # Validate columns
                missing_cols = set(expected_columns) - set(new_df.columns)
                if missing_cols:
                    st.warning(f"Missing columns in uploaded file: {missing_cols}")
                    for col in missing_cols:
                        new_df[col] = ""
                
                new_df = new_df[expected_columns]
                new_df = clean_dataframe(new_df)
                
                # Preview before merge
                st.write("📋 Preview of uploaded data:")
                st.dataframe(new_df.head(), use_container_width=True)
                
                if st.button("✅ Confirm Merge"):
                    original_count = len(df)
                    df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()
                    new_count = len(df)
                    st.session_state.df = df
                    st.success(f"✅ Merged! Added {new_count - original_count} new records.")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error reading CSV: {e}")
        
        # ======= ENHANCED DATA DISPLAY =======
        st.subheader("📊 Data Table")
        
        if not filtered_df.empty:
            # Pagination
            page_size = st.selectbox("Records per page:", [10, 25, 50, 100], index=1)
            total_pages = max(1, (len(filtered_df) - 1) // page_size + 1)
            
            if total_pages > 1:
                page = st.selectbox("Page:", range(1, total_pages + 1))
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                display_df = filtered_df.iloc[start_idx:end_idx]
            else:
                display_df = filtered_df
            
            # Display with enhanced formatting
            try:
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400,
                    column_config={
                        col: st.column_config.TextColumn(
                            col.replace('_', ' ').title(),
                            width="medium"
                        ) for col in expected_columns
                    }
                )
            except Exception as e:
                st.dataframe(display_df, use_container_width=True, height=400)
            
            st.caption(f"Showing {len(display_df)} of {len(filtered_df)} records")
            
            # Row selection for editing
            if not display_df.empty:
                try:
                    selected_idx = st.selectbox(
                        "Select row to edit/delete:",
                        display_df.index,
                        format_func=lambda x: f"Row {x}: {' | '.join(str(display_df.at[x, col])[:20] for col in expected_columns[:2])}"
                    )
                except Exception:
                    selected_idx = display_df.index[0] if len(display_df.index) > 0 else None
            else:
                selected_idx = None
        else:
            st.info("No data to display. Upload a CSV file or add entries manually.")
            selected_idx = None
        
        # ======= ENHANCED EDIT/DELETE =======
        if selected_idx is not None and not df.empty:
            st.subheader("✏️ Edit Selected Record")
            
            with st.form("edit_form"):
                edit_data = {}
                
                # Create dynamic form based on column types
                for col in expected_columns:
                    try:
                        value = df.at[selected_idx, col] if selected_idx in df.index else ""
                        
                        if col == "assessment_date":
                            try:
                                if pd.notna(value) and str(value) != "":
                                    value = pd.to_datetime(value).date()
                                else:
                                    value = datetime.date.today()
                            except:
                                value = datetime.date.today()
                            edit_data[col] = st.date_input(col.replace('_', ' ').title(), value=value)
                        
                        elif col in ['email']:
                            edit_data[col] = st.text_input(
                                col.replace('_', ' ').title(),
                                value=str(value) if pd.notna(value) else "",
                                help="Enter a valid email address"
                            )
                        
                        elif col in ['phone']:
                            edit_data[col] = st.text_input(
                                col.replace('_', ' ').title(),
                                value=str(value) if pd.notna(value) else "",
                                help="Enter phone number with country code"
                            )
                        
                        else:
                            edit_data[col] = st.text_input(
                                col.replace('_', ' ').title(),
                                value=str(value) if pd.notna(value) else ""
                            )
                    except Exception as e:
                        st.warning(f"Error loading field {col}: {e}")
                        edit_data[col] = st.text_input(col.replace('_', ' ').title(), value="")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        # Validate data before saving
                        valid = True
                        
                        if 'email' in edit_data and edit_data['email']:
                            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                            if not re.match(email_pattern, edit_data['email']):
                                st.error("❌ Invalid email format")
                                valid = False
                        
                        if valid:
                            try:
                                for col in expected_columns:
                                    df.at[selected_idx, col] = edit_data[col]
                                st.session_state.df = df
                                st.success("✅ Record updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving changes: {e}")
                
                with col2:
                    if st.form_submit_button("🗑️ Delete Record", type="secondary"):
                        try:
                            df = df.drop(index=selected_idx).reset_index(drop=True)
                            st.session_state.df = df
                            st.success("✅ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
        
        # ======= ENHANCED ADD NEW ENTRY =======
        st.subheader("➕ Add New Record")
        
        with st.form("add_entry_form"):
            new_data = {}
            
            # Create columns for better layout
            form_cols = st.columns(min(3, len(expected_columns)))
            
            for idx, col in enumerate(expected_columns):
                col_idx = idx % len(form_cols)
                
                with form_cols[col_idx]:
                    if col == "assessment_date":
                        new_data[col] = st.date_input(
                            col.replace('_', ' ').title(),
                            value=datetime.date.today()
                        )
                    elif col == "email":
                        new_data[col] = st.text_input(
                            col.replace('_', ' ').title(),
                            placeholder="user@example.com",
                            help="Enter a valid email address"
                        )
                    elif col == "phone":
                        new_data[col] = st.text_input(
                            col.replace('_', ' ').title(),
                            placeholder="+1-234-567-8900",
                            help="Include country code"
                        )
                    else:
                        new_data[col] = st.text_input(
                            col.replace('_', ' ').title(),
                            placeholder=f"Enter {col.replace('_', ' ')}"
                        )
            
            if st.form_submit_button("➕ Add New Record", type="primary"):
                # Validate before adding
                valid = True
                
                if new_data.get('email'):
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, new_data['email']):
                        st.error("❌ Invalid email format")
                        valid = False
                
                if valid:
                    try:
                        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                        df = df.drop_duplicates()
                        st.session_state.df = df
                        st.success("✅ New record added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding record: {e}")
        
        # ======= ENHANCED EXPORT OPTIONS =======
        st.subheader("📥 Export Data")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            # CSV Export
            try:
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv_data,
                    file_name=f"{selected_tab.lower().replace(' ','_')}_{datetime.date.today()}.csv",
                    mime='text/csv'
                )
            except Exception as e:
                st.error(f"CSV export error: {e}")
        
        with export_col2:
            # JSON Export
            try:
                json_data = filtered_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="🔗 Download as JSON",
                    data=json_data,
                    file_name=f"{selected_tab.lower().replace(' ','_')}_{datetime.date.today()}.json",
                    mime='application/json'
                )
            except Exception as e:
                st.error(f"JSON export error: {e}")
        
        # ======= GOOGLE SHEETS SYNC =======
        st.subheader("🔄 Sync with Google Sheets")
        
        def sync_to_gsheet(df, tab_name):
            if not gc:
                st.error("❌ Google authentication required.")
                return False
            
            try:
                sh = gc.open_by_key(SHEET_ID)
                
                # Remove existing worksheet and create new one
                try:
                    worksheet = sh.worksheet(tab_name)
                    sh.del_worksheet(worksheet)
                except gspread.exceptions.WorksheetNotFound:
                    pass
                
                worksheet = sh.add_worksheet(title=tab_name, rows="1000", cols="50")
                
                # Prepare data for upload
                upload_data = [expected_columns] + df.fillna("").astype(str).values.tolist()
                worksheet.update(upload_data)
                
                st.success(f"✅ '{tab_name}' synced successfully!")
                st.info(f"[📊 View in Google Sheets]({SHEET_URL})")
                return True
                
            except Exception as e:
                st.error(f"❌ Sync failed: {e}")
                return False
        
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("🚀 Sync Current Tab", type="primary"):
                with st.spinner("Syncing to Google Sheets..."):
                    sync_to_gsheet(df, selected_tab)
        
        with sync_col2:
            if st.button("🔄 Refresh from Sheets"):
                with st.spinner("Refreshing data..."):
                    try:
                        st.session_state.df = load_gsheet_data(selected_tab)
                        st.success("✅ Data refreshed from Google Sheets!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Refresh error: {e}")

    elif view_mode == "📈 Analytics":
        st.header("📈 Advanced Analytics")
        
        # Load all data for analytics
        all_data = {}
        with st.spinner("Loading analytics data..."):
            for tab_name in tabs_config.keys():
                try:
                    all_data[tab_name] = load_gsheet_data(tab_name)
                except Exception as e:
                    st.warning(f"Could not load {tab_name}: {e}")
                    all_data[tab_name] = pd.DataFrame()
        
        # Analytics tabs
        analytics_tab = st.selectbox(
            "Select Analytics View:",
            ["📊 Overview", "👥 Client Analysis", "📅 Temporal Analysis", "🔍 Data Insights"]
        )
        
        if analytics_tab == "📊 Overview":
            st.subheader("📊 System Overview")
            
            # Create comprehensive metrics
            total_clients = 0
            total_assessments = 0
            active_sections = 0
            
            for name, df in all_data.items():
                if not df.empty:
                    active_sections += 1
                    if 'full_name' in df.columns:
                        try:
                            unique_names = df['full_name'].dropna().unique()
                            total_clients += len(unique_names)
                        except Exception:
                            pass
                    total_assessments += len(df)
            
            # Display overview metrics
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("🎯 Active Sections", active_sections, f"of {len(tabs_config)}")
            
            with metric_cols[1]:
                st.metric("👥 Total Clients", total_clients)
            
            with metric_cols[2]:
                st.metric("📋 Total Records", total_assessments)
            
            with metric_cols[3]:
                avg_records = total_assessments / max(active_sections, 1)
                st.metric("📊 Avg Records/Section", f"{avg_records:.1f}")
            
            # Section activity visualization
            st.subheader("🔥 Section Activity")
            
            activity_data = []
            for name, df in all_data.items():
                try:
                    quality = validate_data_quality(df)
                    activity_data.append({
                        'Section': name,
                        'Records': len(df),
                        'Quality Score': safe_get(quality, 'overall_score', 0),
                        'Completeness': safe_get(quality, 'completeness', 0)
                    })
                except Exception:
                    continue
            
            if activity_data:
                activity_df = pd.DataFrame(activity_data)
                
                try:
                    fig = px.scatter(
                        activity_df,
                        x='Records',
                        y='Quality Score',
                        size='Completeness',
                        color='Completeness',
                        hover_name='Section',
                        title="Section Performance Matrix",
                        labels={'Quality Score': 'Data Quality (%)', 'Records': 'Number of Records'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating scatter plot: {e}")
                    st.dataframe(activity_df)
        
        elif analytics_tab == "👥 Client Analysis":
            st.subheader("👥 Client Demographics Analysis")
            
            basic_info = all_data.get('Basic Info', pd.DataFrame())
            
            if not basic_info.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Industry distribution
                    if 'industry' in basic_info.columns:
                        try:
                            industry_counts = basic_info['industry'].value_counts()
                            if not industry_counts.empty:
                                fig = px.pie(
                                    values=industry_counts.values,
                                    names=industry_counts.index,
                                    title="Client Distribution by Industry"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Industry chart error: {e}")
                
                with col2:
                    # Company size distribution
                    if 'company_size' in basic_info.columns:
                        try:
                            size_counts = basic_info['company_size'].value_counts()
                            if not size_counts.empty:
                                fig = px.bar(
                                    x=size_counts.index,
                                    y=size_counts.values,
                                    title="Distribution by Company Size",
                                    labels={'x': 'Company Size', 'y': 'Count'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.error(f"Company size chart error: {e}")
                
                # Geographic analysis
                contact_info = all_data.get('Contact Info', pd.DataFrame())
                if not contact_info.empty and 'state' in contact_info.columns:
                    st.subheader("🗺️ Geographic Distribution")
                    try:
                        state_counts = contact_info['state'].value_counts().head(10)
                        
                        fig = px.bar(
                            x=state_counts.values,
                            y=state_counts.index,
                            orientation='h',
                            title="Top 10 States by Client Count",
                            labels={'x': 'Number of Clients', 'y': 'State'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Geographic chart error: {e}")
            
            else:
                st.info("No client data available for analysis")
        
        elif analytics_tab == "📅 Temporal Analysis":
            st.subheader("📅 Time-based Analysis")
            
            basic_info = all_data.get('Basic Info', pd.DataFrame())
            
            if not basic_info.empty and 'assessment_date' in basic_info.columns:
                try:
                    # Convert dates
                    basic_info['assessment_date'] = pd.to_datetime(basic_info['assessment_date'], errors='coerce')
                    valid_dates = basic_info.dropna(subset=['assessment_date'])
                    
                    if not valid_dates.empty:
                        # Monthly trend
                        monthly_counts = valid_dates.groupby(valid_dates['assessment_date'].dt.to_period('M')).size()
                        
                        fig = px.line(
                            x=monthly_counts.index.astype(str),
                            y=monthly_counts.values,
                            title="Assessment Trends Over Time",
                            labels={'x': 'Month', 'y': 'Number of Assessments'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Day of week analysis
                        valid_dates['day_of_week'] = valid_dates['assessment_date'].dt.day_name()
                        dow_counts = valid_dates['day_of_week'].value_counts()
                        
                        fig = px.bar(
                            x=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                            y=[dow_counts.get(day, 0) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
                            title="Assessments by Day of Week",
                            labels={'x': 'Day of Week', 'y': 'Count'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No valid dates found for analysis")
                except Exception as e:
                    st.error(f"Temporal analysis error: {e}")
            else:
                st.info("No date data available for temporal analysis")
        
        elif analytics_tab == "🔍 Data Insights":
            st.subheader("🔍 Advanced Data Insights")
            
            # Data completeness analysis
            completeness_data = []
            for name, df in all_data.items():
                if not df.empty:
                    for col in df.columns:
                        try:
                            non_empty = df[col].notna().sum() + (df[col].astype(str) != "").sum()
                            completeness = (non_empty / len(df)) * 100 if len(df) > 0 else 0
                            completeness_data.append({
                                'Section': name,
                                'Field': col,
                                'Completeness': completeness,
                                'Records': len(df)
                            })
                        except Exception:
                            continue
            
            if completeness_data:
                completeness_df = pd.DataFrame(completeness_data)
                
                try:
                    # Heatmap of field completeness
                    pivot_df = completeness_df.pivot(index='Section', columns='Field', values='Completeness')
                    
                    fig = px.imshow(
                        pivot_df.values,
                        x=pivot_df.columns,
                        y=pivot_df.index,
                        color_continuous_scale='RdYlGn',
                        title="Field Completeness Heatmap (%)",
                        aspect='auto'
                    )
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Heatmap error: {e}")
                    st.dataframe(completeness_df)
                
                # Top incomplete fields
                st.subheader("⚠️ Fields Needing Attention")
                incomplete_fields = completeness_df[completeness_df['Completeness'] < 80].sort_values('Completeness')
                
                if not incomplete_fields.empty:
                    try:
                        fig = px.bar(
                            incomplete_fields.head(10),
                            x='Completeness',
                            y='Field',
                            color='Section',
                            orientation='h',
                            title="Top 10 Incomplete Fields",
                            labels={'Completeness': 'Completeness (%)', 'Field': 'Field Name'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Incomplete fields chart error: {e}")
                        st.dataframe(incomplete_fields.head(10))
                else:
                    st.success("🎉 All fields have good completeness (>80%)!")
            else:
                st.info("No data available for insights analysis")

    elif view_mode == "⚙️ Settings":
        st.header("⚙️ System Settings")
        
        # Configuration settings
        st.subheader("📋 Tab Configuration")
        
        for tab_name, config in tabs_config.items():
            with st.expander(f"{config['icon']} {tab_name}"):
                st.write(f"**Description:** {config['description']}")
                st.write(f"**Columns:** {len(config['columns'])}")
                st.code(", ".join(config['columns']))
        
        # System information
        st.subheader("ℹ️ System Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.info(f"""
            **Google Sheet ID:** `{SHEET_ID}`
            **Total Sections:** {len(tabs_config)}
            **Authentication:** {'✅ Connected' if gc else '❌ Not Connected'}
            """)
        
        with info_col2:
            st.info(f"""
            **Cache TTL:** 5 minutes
            **Page Size Options:** 10, 25, 50, 100
            **Export Formats:** CSV, JSON
            """)
        
        # Data management tools
        st.subheader("🛠️ Data Management Tools")
        
        if st.button("🔄 Clear All Cache"):
            st.cache_data.clear()
            st.success("✅ Cache cleared successfully!")
        
        if st.button("📊 Regenerate Dashboard"):
            if 'df' in st.session_state:
                del st.session_state.df
            st.success("✅ Dashboard will regenerate on next view!")

except Exception as e:
    st.error(f"❌ Application Error: {e}")
    st.info("Please try refreshing the page or contact support if the issue persists.")

# ======= FOOTER =======
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Enhanced CRM Client Profiles Manager</strong></p>
    <p>🚀 Advanced Analytics • 📊 Data Insights • 🔄 Real-time Sync</p>
    <p>Built with ❤️ using Streamlit + Google Sheets + Plotly</p>
</div>
""", unsafe_allow_html=True)
