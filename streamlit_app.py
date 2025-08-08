import datetime
import random
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit_sortables
from pymongo import MongoClient
from streamlit_sortables import sort_items

# MongoDB setup
MONGO_URI = "mongodb+srv://slugics:B8KaWcLehYvwkNHF@cluster0.xc2qsoh.mongodb.net/"
DB_NAME = "tasktickets"
COLLECTION_NAME = "tasks"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def fetch_tasks():
    # Exclude _id field from MongoDB results to avoid Arrow/Streamlit errors
    tasks = list(collection.find({}, {"_id": 0}))
    if not tasks:
        # Seed initial data if empty
        np.random.seed(42)
        task_descriptions = [
            "Network connectivity issues in the office",
            "Software application crashing on startup",
            "Printer not responding to print commands",
            "Email server downtime",
            "Data backup failure",
            "Login authentication problems",
            "Website performance degradation",
            "Security vulnerability identified",
            "Hardware malfunction in the server room",
            "Employee unable to access shared files",
            "Database connection failure",
            "Mobile application not syncing data",
            "VoIP phone system issues",
            "VPN connection problems for remote employees",
            "System updates causing compatibility issues",
            "File server running out of storage space",
            "Intrusion detection system alerts",
            "Inventory management system errors",
            "Customer data not loading in CRM",
            "Collaboration tool not sending notifications",
        ]
        data = [{
            "ID": f"Task-{i:04d}",
            "Task": str(np.random.choice(task_descriptions)),
            "Status": str(np.random.choice(["Open", "In Progress", "Closed"])),
            "Priority": str(np.random.choice(["High", "Medium", "Low"])),
            "Date Submitted": (datetime.date(2023, 6, 1) + datetime.timedelta(days=random.randint(0, 182))).strftime("%Y-%m-%d"),
            "Due Date": "2025-08-15",
        } for i in range(1100, 1000, -1)]
        collection.insert_many(data)
        tasks = data
    # Sort by ID descending (most recent first)
    df = pd.DataFrame(tasks)
    if not df.empty:
        df["ID_num"] = df["ID"].apply(lambda x: int(x.split("-")[1]))
        df = df.sort_values("ID_num", ascending=False).drop(columns=["ID_num"])
        df = df.reset_index(drop=True)
    return df


def add_task(task, priority, due_date):
    recent = collection.find_one(sort=[("ID", -1)])
    if recent:
        recent_task_number = int(recent["ID"].split("-")[1])
    else:
        recent_task_number = 1100
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    new_task = {
        "ID": f"Task-{recent_task_number+1:04d}",
        "Task": task,
        "Status": "Open",
        "Priority": priority,
        "Date Submitted": today,
        "Due Date": due_date.strftime("%Y-%m-%d"),
    }
    collection.insert_one(new_task)
    return new_task


def update_tasks(df):
    # Convert any datetime.date objects to string before inserting
    df = df.copy()
    if "Due Date" in df.columns:
        df["Due Date"] = df["Due Date"].apply(lambda x: x.strftime(
            "%Y-%m-%d") if isinstance(x, datetime.date) else str(x))
    if "Date Submitted" in df.columns:
        df["Date Submitted"] = df["Date Submitted"].apply(
            lambda x: x.strftime("%Y-%m-%d") if isinstance(x, datetime.date) else str(x))
    collection.delete_many({})
    collection.insert_many(df.to_dict("records"))


def delete_task(task_id):
    collection.delete_one({"ID": task_id})


def ensure_due_date_is_date(df):
    # Ensure Due Date is always datetime.date for compatibility with st.data_editor
    df = df.copy()
    if "Due Date" in df.columns:
        df["Due Date"] = pd.to_datetime(
            df["Due Date"], errors="coerce").dt.date
    return df


# Show app title and description.
st.set_page_config(page_title="Task Tickets", page_icon="🎫")
st.title("🎫 Task Tickets")
st.write(
    """
    This app shows how you can build an internal tool in Streamlit. Here, we are
    implementing a task ticket workflow. The user can create a task ticket, edit
    existing task tickets, and view some statistics.
    """
)

# Load tasks from MongoDB
if "df" not in st.session_state:
    st.session_state.df = fetch_tasks()
    st.session_state.df = ensure_due_date_is_date(st.session_state.df)

# Add a new task ticket
st.header("Add a task ticket")
with st.form("add_task_ticket_form"):
    task = st.text_area("Describe the task")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    due_date = st.date_input("Due Date", value=datetime.date(2025, 8, 15))
    submitted = st.form_submit_button("Submit")

if submitted:
    new_task = add_task(task, priority, due_date)
    df_new = pd.DataFrame([new_task])
    st.write("Task ticket submitted! Here are the ticket details:")
    st.dataframe(df_new, use_container_width=True, hide_index=True)
    st.session_state.df = fetch_tasks()
    st.session_state.df = ensure_due_date_is_date(
        st.session_state.df)  # Ensure correct type after adding

# Tabs for Table and Board View
tab_table = st.container()

with tab_table:
    # View and edit existing tickets
    st.header("Existing task tickets")

    # Column visibility controls
    st.subheader("Column Visibility")
    col_vis1, col_vis2, col_vis3 = st.columns(3)
    
    with col_vis1:
        show_id = st.checkbox("Show ID", value=True)
        show_task = st.checkbox("Show Task", value=True)
        show_status = st.checkbox("Show Status", value=True)
    
    with col_vis2:
        show_priority = st.checkbox("Show Priority", value=True)
        show_date_submitted = st.checkbox("Show Date Submitted", value=True)
        show_due_date = st.checkbox("Show Due Date", value=True)
    
    with col_vis3:
        show_delete = st.checkbox("Show Delete Column", value=True)

    # Single dropdown for filter type, then show appropriate filter
    filter_type = st.selectbox("Filter by...", ["None", "Status", "Priority"])
    filtered_df = st.session_state.df.copy()
    if filter_type == "Status":
        status_options = sorted(st.session_state.df["Status"].unique())
        selected_status = st.selectbox("Select Status", status_options)
        filtered_df = filtered_df[filtered_df.Status == selected_status]
    elif filter_type == "Priority":
        priority_options = sorted(st.session_state.df["Priority"].unique())
        selected_priority = st.selectbox("Select Priority", priority_options)
        filtered_df = filtered_df[filtered_df.Priority == selected_priority]

    st.write(f"Number of task tickets: `{len(filtered_df)}`")
    st.info(
        "You can edit the task tickets by double clicking on a cell. Note how the plots below "
        "update automatically! You can also sort the table by clicking on the column headers.",
        icon="✍️",
    )

    st.session_state.df = fetch_tasks()  # Always fetch sorted
    st.session_state.df = ensure_due_date_is_date(st.session_state.df)
    # Ensure correct type before editing
    filtered_df = ensure_due_date_is_date(filtered_df)
    
    # Add delete column if needed
    if show_delete:
        filtered_df["Delete"] = False

    # Filter columns based on visibility settings
    columns_to_show = []
    if show_id:
        columns_to_show.append("ID")
    if show_task:
        columns_to_show.append("Task")
    if show_status:
        columns_to_show.append("Status")
    if show_priority:
        columns_to_show.append("Priority")
    if show_date_submitted:
        columns_to_show.append("Date Submitted")
    if show_due_date:
        columns_to_show.append("Due Date")
    if show_delete:
        columns_to_show.append("Delete")
    
    # Filter the dataframe to only show selected columns
    display_df = filtered_df[columns_to_show]

    # Build column config based on visible columns
    column_config = {}
    disabled_cols = []
    
    if show_status:
        column_config["Status"] = st.column_config.SelectboxColumn(
            "Status",
            help="Task ticket status",
            options=["Open", "In Progress", "Closed"],
            required=True,
        )
    
    if show_priority:
        column_config["Priority"] = st.column_config.SelectboxColumn(
            "Priority",
            help="Priority",
            options=["High", "Medium", "Low"],
            required=True,
        )
    
    if show_due_date:
        column_config["Due Date"] = st.column_config.DateColumn(
            "Due Date",
            help="Due date for the task",
            format="YYYY-MM-DD",
            required=True,
        )
    
    if show_delete:
        column_config["Delete"] = st.column_config.CheckboxColumn(
            "❌",
            help="Check to delete this task",
            width="small",
        )
    
    if show_id:
        disabled_cols.append("ID")
    if show_date_submitted:
        disabled_cols.append("Date Submitted")

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        disabled=disabled_cols,
        key="task_editor",
        num_rows="fixed"
    )

    # Handle deletions
    if show_delete and "Delete" in edited_df.columns:
        tasks_to_delete = edited_df[edited_df["Delete"] == True]
        if not tasks_to_delete.empty:
            for _, task in tasks_to_delete.iterrows():
                delete_task(task["ID"])
            st.session_state.df = fetch_tasks()
            st.session_state.df = ensure_due_date_is_date(st.session_state.df)
            st.success(f"Deleted {len(tasks_to_delete)} task(s).")
            st.rerun()
    
    # Handle other edits (remove Delete column before comparison if it exists)
    edited_df_clean = edited_df.drop(columns=["Delete"]) if "Delete" in edited_df.columns else edited_df
    display_df_clean = display_df.drop(columns=["Delete"]) if "Delete" in display_df.columns else display_df
    
    if not edited_df_clean.equals(display_df_clean):
        # Map the edited data back to the full dataframe
        for idx, row in edited_df_clean.iterrows():
            if "ID" in row:
                task_id = row["ID"]
                mask = st.session_state.df["ID"] == task_id
                for col in edited_df_clean.columns:
                    if col in st.session_state.df.columns:
                        st.session_state.df.loc[mask, col] = row[col]
        
        update_tasks(st.session_state.df)
        st.session_state.df = fetch_tasks()
        st.success("Changes saved.")

    # Statistics
    st.header("Statistics")
    col1, col2, col3 = st.columns(3)
    num_open_task_tickets = len(filtered_df[filtered_df.Status == "Open"])
    col1.metric(label="Number of open task tickets",
                value=num_open_task_tickets, delta=10)
    col2.metric(label="First response time (hours)", value=5.2, delta=-1.5)
    col3.metric(label="Average resolution time (hours)", value=16, delta=2)

    st.write("")
    st.write("##### Task ticket status per month")
    status_plot = (
        alt.Chart(filtered_df)
        .mark_bar()
        .encode(
            x="month(Date Submitted):O",
            y="count():Q",
            xOffset="Status:N",
            color="Status:N",
        )
        .configure_legend(
            orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
        )
    )
    st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

    st.write("##### Current task ticket priorities")
    priority_plot = (
        alt.Chart(filtered_df)
        .mark_arc()
        .encode(theta="count():Q", color="Priority:N")
        .properties(height=300)
        .configure_legend(
            orient="bottom", titleFontSize=14, labelFontSize=14, titlePadding=5
        )
    )
    st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")
