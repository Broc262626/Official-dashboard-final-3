
import streamlit as st
import pandas as pd
import io
import plotly.express as px
from pathlib import Path
import base64
from datetime import datetime

st.set_page_config(page_title="Cameras & Tasks Repair Dashboard", page_icon="assets/logo.png", layout="wide")

DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
CSV_FILE = DATA_PATH / "devices.csv"

STATUS_OPTIONS = [
    "New",
    "Inspected, all good",
    "Inspected, Awaiting PO approval",
    "PO approved to be repaired",
    "Repaired, all good"
]

def load_data():
    if CSV_FILE.exists():
        try:
            return pd.read_csv(CSV_FILE, dtype=str)
        except Exception:
            return pd.read_csv(CSV_FILE, dtype=str, encoding='latin1')
    else:
        cols=["id","server","parent_fleet","fleet_number","registration","status","comments","date_created","priority","assigned_to"]
        df = pd.DataFrame(columns=cols)
        df.to_csv(CSV_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def make_download_link(df, filename="devices_export.csv"):
    towrite = io.BytesIO()
    df.to_csv(towrite, index=False)
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'

# Simple auth (example)
CREDENTIALS = {
    "admin": {"password":"admin123","role":"admin"},
    "viewer": {"password":"viewer123","role":"viewer"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

def login():
    st.image("assets/logo.png", width=140)
    st.title("Cameras & Tasks Repair Dashboard")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = CREDENTIALS.get(username)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.success("Login successful — loading dashboard...")
                st.stop()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.experimental_rerun()

# Styling helper: highlight priority 1 (red), 2 (yellow), 3 (green)
def highlight_priority(row):
    try:
        pr = int(row.get("priority", 0))
    except:
        pr = 0
    if pr == 1:
        return ["background-color: #ffcccc; font-weight:700;" for _ in row.index]
    elif pr == 2:
        return ["background-color: #fff3bf;" for _ in row.index]
    elif pr == 3:
        return ["background-color: #e6ffed;" for _ in row.index]
    return ["",]*len(row.index)

def main_dashboard():
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Go to", ["Overview","Table / Records","Import / Export","Analytics","About"])
    df = load_data()

    if page == "Overview":
        st.header("Overview")
        counts = {s: int((df['status']==s).sum()) if 'status' in df.columns else 0 for s in STATUS_OPTIONS}
        cols = st.columns(len(STATUS_OPTIONS))
        colors = ["#f0f8ff","#e6f2ff","#fff4e6","#e6fff0","#e8f7e8"]
        for i, s in enumerate(STATUS_OPTIONS):
            with cols[i]:
                st.markdown(f'<div style="padding:14px;border-radius:8px;background:{colors[i]};box-shadow:0 2px 6px rgba(0,0,0,0.08)">' + 
                            f'<h4 style="margin:0;color:#0b3b5c">{s}</h4>' +
                            f'<p style="font-size:22px;margin:6px 0 0 0;color:#0b1b2b">{counts[s]}</p>' +
                            '</div>', unsafe_allow_html=True)

    elif page == "Table / Records":
        st.header("Devices / Records")
        st.write("Columns: Server, Parent fleet, Fleet number, Registration, Status, Comments, Date created, Priority, Assigned to")
        # Filters inside Table / Records (removes top search)
        with st.expander("Filters", expanded=True):
            q_status = st.selectbox("Status", options=['All'] + STATUS_OPTIONS)
            q_fleet = st.text_input("Parent fleet")
            q_priority = st.selectbox("Priority", options=['All','1','2','3'])
        filtered = df.copy()
        if q_status and q_status != 'All':
            filtered = filtered[filtered['status']==q_status]
        if q_fleet:
            filtered = filtered[filtered['parent_fleet'].str.contains(q_fleet, na=False, case=False)]
        if q_priority and q_priority != 'All':
            filtered = filtered[filtered['priority']==q_priority]

        # Ensure priority numeric where possible for sorting/display
        try:
            filtered['priority'] = filtered['priority'].astype(int)
        except:
            pass
        filtered = filtered.sort_values(by='priority', na_position='last')

        # Display styled table with priority colors
        try:
            styled = filtered.style.apply(highlight_priority, axis=1)
            st.write(styled.to_html(), unsafe_allow_html=True)
        except Exception:
            st.dataframe(filtered, use_container_width=True)

        # Remove Add New Record. Provide Edit / Delete for admin only.
        if st.session_state.role == 'admin':
            st.markdown("---")
            st.subheader("Edit / Delete record")
            with st.form("edit_form"):
                options = [''] + df['id'].fillna('').tolist() if 'id' in df.columns else ['']
                edit_id = st.selectbox("Select record ID to edit", options=options)
                if edit_id:
                    row = df[df['id']==edit_id].iloc[0].to_dict()
                    e_server = st.text_input("Server", value=row.get("server",""))
                    e_parent = st.text_input("Parent fleet", value=row.get("parent_fleet",""))
                    e_fleet = st.text_input("Fleet number", value=row.get("fleet_number",""))
                    e_reg = st.text_input("Registration", value=row.get("registration",""))
                    e_status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(row.get("status")) if row.get("status") in STATUS_OPTIONS else 0)
                    e_comments = st.text_area("Comments", value=row.get("comments",""), height=150)
                    e_date = st.text_input("Date created", value=row.get("date_created",""))
                    e_priority = st.selectbox("Priority", ['1','2','3'], index=0 if str(row.get("priority",""))=='1' else (1 if str(row.get("priority",""))=='2' else 2))
                    e_assigned = st.text_input("Assigned to", value=row.get("assigned_to",""))
                    if st.form_submit_button("Save changes"):
                        df.loc[df['id']==edit_id, 'server'] = e_server
                        df.loc[df['id']==edit_id, 'parent_fleet'] = e_parent
                        df.loc[df['id']==edit_id, 'fleet_number'] = e_fleet
                        df.loc[df['id']==edit_id, 'registration'] = e_reg
                        df.loc[df['id']==edit_id, 'status'] = e_status
                        df.loc[df['id']==edit_id, 'comments'] = e_comments
                        df.loc[df['id']==edit_id, 'date_created'] = e_date
                        df.loc[df['id']==edit_id, 'priority'] = e_priority
                        df.loc[df['id']==edit_id, 'assigned_to'] = e_assigned
                        save_data(df)
                        st.success("Saved")
                        st.experimental_rerun()
                if st.form_submit_button("Delete selected"):
                    if edit_id:
                        df = df[df['id']!=edit_id]
                        save_data(df)
                        st.success("Deleted")
                        st.experimental_rerun()

    elif page == "Import / Export":
        st.header("Import & Export")
        st.subheader("Export current data")
        st.markdown(make_download_link(df, "devices_export.csv"), unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Import CSV / Excel")
        uploaded = st.file_uploader("Upload CSV or Excel", type=['csv','xlsx'])
        if uploaded:
            try:
                if uploaded.name.endswith('.csv'):
                    newdf = pd.read_csv(uploaded, dtype=str)
                else:
                    newdf = pd.read_excel(uploaded, dtype=str)
                save_data(newdf)
                st.success("Imported successfully")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to import: {e}")

    elif page == "Analytics":
        st.header("Analytics")
        if 'status' in df.columns:
            counts = df['status'].value_counts().reset_index()
            counts.columns = ['status','count']
            st.subheader("Counts by status")
            st.table(counts)
            st.subheader("Bar chart")
            fig = px.bar(counts, x='status', y='count', title="Devices by Status")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status column present.")

    elif page == "About":
        st.header("About this dashboard")
        st.write("Modern Streamlit layout with cards & tables. Theme colors: soft blue / gray. Priority 1 highlighted in red-ish background.")

if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
