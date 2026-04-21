import streamlit as st
import pandas as pd
from collections import defaultdict
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

st.set_page_config(page_title="Potluck Coordinator", layout="wide")

st.title("🍲 Office Potluck Coordinator")

# ---------------- GOOGLE SHEETS SETUP ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)
sheet = client.open("Potluck").sheet1

# Ensure header exists
if sheet.row_values(1) != ["Name", "Category", "Dish"]:
    sheet.clear()
    sheet.append_row(["Name", "Category", "Dish"])

# ---------------- CATEGORY CONFIG ----------------
CATEGORY_CONFIG = {
    "Starters Veg": {"variety_limit": 2, "min_people": 1, "max_people": 3},
    "Starters Nonveg": {"variety_limit": 2, "min_people": 1, "max_people": 3},
    "Main Course Veg": {"variety_limit": 1, "min_people": 2, "max_people": 5},
    "Main Course Non-Veg": {"variety_limit": 1, "min_people": 2, "max_people": 5},
    "Roti": {"variety_limit": 2, "min_people": 2, "max_people": 5},
    "Veg Curry": {"variety_limit": 1, "min_people": 2, "max_people": 2},
    "Nonveg Curry": {"variety_limit": 1, "min_people": 2, "max_people": 2},
    "Salads": {"variety_limit": 1, "min_people": 1, "max_people": 2},
    "Desserts": {"variety_limit": 2, "min_people": 1, "max_people": 2}
}

# ---------------- LOAD DATA ----------------
data = sheet.get_all_records()
df_entries = pd.DataFrame(data)

if df_entries.empty:
    df_entries = pd.DataFrame(columns=["Name", "Category", "Dish"])

# Build structured data
category_data = defaultdict(lambda: defaultdict(list))
for _, row in df_entries.iterrows():
    category_data[row["Category"]][row["Dish"]].append(row["Name"])

# ---------------- LAYOUT ----------------
col1, col2 = st.columns([1, 2])

# ---------- LEFT: FORM ----------
with col1:
    st.subheader("➕ Manage Contribution")

    name = st.text_input("Your Name")

    # Remove self
    if st.button("Remove Myself"):
        if not name:
            st.warning("Enter your name")
        else:
            updated = df_entries[df_entries["Name"] != name]
            sheet.clear()
            sheet.append_row(["Name", "Category", "Dish"])
            for _, r in updated.iterrows():
                sheet.append_row([r["Name"], r["Category"], r["Dish"]])
            st.success("Removed successfully")
            st.rerun()

    st.markdown("---")

    category = st.selectbox("Category", list(CATEGORY_CONFIG.keys()))
    config = CATEGORY_CONFIG[category]
    dishes = category_data[category]

    # Dish selection
    dish_options = list(dishes.keys())
    dish_choice = st.selectbox("Select Dish", ["+ Add New Dish"] + dish_options)

    if dish_choice == "+ Add New Dish":
        dish = st.text_input("Enter New Dish Name")
    else:
        dish = dish_choice

    # Info text
    st.info(f"Max varieties: {config['variety_limit']} | Contributors per dish: {config['min_people']}–{config['max_people']}")

    # Validation
    is_new_dish = dish not in dishes
    current_varieties = len(dishes)
    current_people = len(dishes[dish]) if dish in dishes else 0

    duplicate_name = name in df_entries["Name"].values

    if duplicate_name:
        st.warning("You already have an entry. Remove and re-add if needed.")

    if st.button("Submit", use_container_width=True):
        if not name or not dish:
            st.error("Fill all fields")
        elif duplicate_name:
            st.error("Duplicate name not allowed")
        elif is_new_dish and current_varieties >= config["variety_limit"]:
            st.error("Variety limit reached")
        elif not is_new_dish and current_people >= config["max_people"]:
            st.error("Dish already full")
        else:
            sheet.append_row([name, category, dish])
            st.success("Added successfully")
            st.rerun()

# ---------- RIGHT: DASHBOARD ----------
with col2:
    st.subheader("📊 Live Potluck Status")

    rows = []

    for category, config in CATEGORY_CONFIG.items():
        dishes = category_data[category]

        for dish, people in dishes.items():
            count = len(people)

            if count < config["min_people"]:
                status = "Underfilled"
            elif count >= config["max_people"]:
                status = "Full"
            else:
                status = "In Progress"

            rows.append({
                "Category": category,
                "Dish": dish,
                "Contributors": ", ".join(people),
                "Count": count,
                "Status": status
            })

        if not dishes:
            rows.append({
                "Category": category,
                "Dish": "—",
                "Contributors": "—",
                "Count": 0,
                "Status": "No entries"
            })

    df = pd.DataFrame(rows)

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Metrics
    total_people = len(df_entries)
    total_dishes = sum(len(d) for d in category_data.values())

    m1, m2 = st.columns(2)
    m1.metric("Total Contributors", total_people)
    m2.metric("Total Dishes", total_dishes)

    # Download section
    st.subheader("⬇️ Download Data")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "potluck.csv", "text/csv")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("Download Excel", output.getvalue(), "potluck.xlsx")
