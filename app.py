
import streamlit as st
import pandas as pd
import json, hashlib, time, os
from datetime import datetime

st.set_page_config(page_title="Device Dashboard (PBKDF2 auth)", layout="wide")

USERS_FILE = "users.json"
REPAIRS_FILE = "repairs.csv"
LOGS_FILE = "logs.csv"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE,"r") as f:
            return json.load(f)
    return {}

def verify_password_pbkdf2(password, user_record):
    salt = user_record.get("salt")
    iterations = int(user_record.get("iterations", 200000))
    expected = user_record.get("hash")
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return dk.hex() == expected

def log_action(user, action, details=""):
    timestamp = datetime.utcnow().isoformat()
    entry = {"timestamp": timestamp, "user": user, "action": action, "details": details}
    if os.path.exists(LOGS_FILE):
        df = pd.read_csv(LOGS_FILE, dtype=str)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:
        df = pd.DataFrame([entry])
    df.to_csv(LOGS_FILE, index=False)

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = "readonly"

st.sidebar.title("Login / Theme")
users = load_users()

if st.session_state.user is None:
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Log in"):
        if username in users and verify_password_pbkdf2(password, users[username]):
            st.session_state.user = username
            st.session_state.role = "admin" if username == "admin" else "readonly"
            log_action(username, "login", "success")
            st.experimental_rerun()
        else:
            st.sidebar.error("Invalid credentials")
else:
    st.sidebar.markdown(f"**Logged in:** {st.session_state.user} ({st.session_state.role})")
    if st.sidebar.button("Log out"):
        log_action(st.session_state.user, "logout", "")
        st.session_state.user = None
        st.session_state.role = "readonly"
        st.experimental_rerun()

# Navigation
page = st.sidebar.radio("Go to", ["Dashboard","Add/Edit Devices","Admin settings","Analytics","Reports/Logs"])

# Load repairs
if os.path.exists(REPAIRS_FILE):
    df = pd.read_csv(REPAIRS_FILE, dtype=str).fillna("")
else:
    df = pd.DataFrame(columns=["Server","Parent fleet","Fleet number","Issue","Priority","Tech Support check","Status"])

# Simple PBKDF2-authenticated UI
if page == "Dashboard":
    st.title("Dashboard")
    st.metric("Total Devices", len(df))
    st.subheader("Device table")
    st.dataframe(df, use_container_width=True)

elif page == "Add/Edit Devices":
    st.title("Add / Edit Devices")
    if st.session_state.role != "admin":
        st.info("Read-only: log in as admin to add/edit/delete")
    with st.form("add_form"):
        s = st.text_input("Server")
        pf = st.text_input("Parent fleet")
        fn = st.text_input("Fleet number")
        issue = st.text_area("Issue", height=150)
        pr = st.selectbox("Priority", ["1","2","3"])
        tech = st.selectbox("Tech Support check", ["Yes","No"])
        stt = st.selectbox("Status", ["New","Incomplete","waiting materials","Complete"])
        if st.form_submit_button("Add"):
            df.loc[len(df)] = [s,pf,fn,issue,pr,tech,stt]
            df.to_csv(REPAIRS_FILE, index=False)
            log_action(st.session_state.user or "anonymous", "add", f"{s} | {pf} | {fn}")
            st.success("Added")
            time.sleep(0.2)
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Delete record (Admin only)")
    if st.session_state.role == "admin" and len(df) > 0:
        del_idx = st.number_input("Row index to delete", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete record"):
            rec = df.loc[int(del_idx)].to_dict()
            df = df.drop(int(del_idx)).reset_index(drop=True)
            df.to_csv(REPAIRS_FILE, index=False)
            log_action(st.session_state.user, "delete", str(rec))
            st.success("Deleted")
            st.experimental_rerun()

elif page == "Admin settings":
    st.title("Admin settings")
    if st.session_state.role != "admin":
        st.info("Only admin can manage users")
    else:
        st.subheader("Users")
        st.write(list(users.keys()))
        with st.expander("Create user"):
            uname = st.text_input("New username")
            pwd = st.text_input("Password", type="password")
            if st.button("Create user"):
                # create pbkdf2 entry and save to users.json
                salt = secrets.token_hex(16)
                dk = hashlib.pbkdf2_hmac("sha256", pwd.encode('utf-8'), salt.encode('utf-8'), 200000)
                users[uname] = {"salt": salt, "iterations": 200000, "hash": dk.hex()}
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f, indent=2)
                log_action(st.session_state.user, "create_user", uname)
                st.success("User created")

elif page == "Analytics":
    st.title("Analytics")
    st.write("Charts coming soon")

elif page == "Reports/Logs":
    st.title("Reports & Logs")
    if os.path.exists(LOGS_FILE):
        st.dataframe(pd.read_csv(LOGS_FILE), use_container_width=True)
    else:
        st.info("No logs yet")
