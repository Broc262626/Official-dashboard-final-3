
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Repairs Dashboard", layout="wide")

st.title("Repairs Dashboard")

# Load data
df = pd.read_csv("data/devices.csv")

st.subheader("Edit Record")

if len(df) > 0:
    row_to_edit = st.selectbox("Select record to edit", df.index.tolist())

    if st.button("Load record"):
        st.session_state['edit_row'] = row_to_edit

    if 'edit_row' in st.session_state:
        row = st.session_state['edit_row']
        server = st.text_input("Server", df.at[row, "Server"])
        parent = st.text_input("Parent Fleet", df.at[row, "ParentFleet"])
        fleetnum = st.text_input("Fleet Number", df.at[row, "FleetNumber"])
        reg = st.text_input("Registration", df.at[row, "Registration"])
        status = st.text_input("Status", df.at[row, "Status"])
        comments = st.text_area("Comments", df.at[row, "Comments"], height=200)
        date = st.text_input("Date Created", df.at[row, "DateCreated"])
        priority = st.selectbox("Priority", ["1","2","3"], index=["1","2","3"].index(str(df.at[row, "Priority"])) if str(df.at[row, "Priority"]) in ["1","2","3"] else 0)

        if st.button("Save Changes"):
            df.at[row, "Server"] = server
            df.at[row, "ParentFleet"] = parent
            df.at[row, "FleetNumber"] = fleetnum
            df.at[row, "Registration"] = reg
            df.at[row, "Status"] = status
            df.at[row, "Comments"] = comments
            df.at[row, "DateCreated"] = date
            df.at[row, "Priority"] = priority
            df.to_csv("data/devices.csv", index=False)
            st.success("Record updated successfully!")
else:
    st.write("No records available to edit.")

st.subheader("Records Table with Priority Colors")

def highlight_priority(row):
    if str(row["Priority"]) == "1":
        return ["background-color: #ff4d4d"] * len(row)
    elif str(row["Priority"]) == "2":
        return ["background-color: #ffe066"] * len(row)
    elif str(row["Priority"]) == "3":
        return ["background-color: #85e085"] * len(row)
    return [""] * len(row)

st.dataframe(df.style.apply(highlight_priority, axis=1), use_container_width=True)

st.subheader("Analytics")

if "Status" in df.columns and df["Status"].notna().sum() > 0:
    st.bar_chart(df["Status"].value_counts())
else:
    st.write("No status data available.")
