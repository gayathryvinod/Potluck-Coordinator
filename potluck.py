import streamlit as st
import pandas as pd
from collections import defaultdict

st.set_page_config(page_title="Potluck Coordinator", layout="wide")

st.title("🍲 Office Potluck Coordinator")

# Category configuration
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

# Session state
if "entries" not in st.session_state:
    st.session_state.entries = []

# Build structured data
category_data = defaultdict(lambda: defaultdict(list))
for entry in st.session_state.entries:
    category_data[entry["category"]][entry["dish"]].append(entry["name"])

# Layout
col1, col2 = st.columns([1, 2])

# ---------- LEFT: FORM ----------
with col1:
    st.subheader("➕ Manage Contribution")

    name = st.text_input("Your Name")

    # Remove self option
    if st.button("Remove Myself"):
        if not name:
            st.warning("Enter your name to remove entries")
        else:
            original_len = len(st.session_state.entries)
            st.session_state.entries = [e for e in st.session_state.entries if e["name"] != name]
            if len(st.session_state.entries) < original_len:
                st.success("Your entries were removed")
                st.rerun()
            else:
                st.warning("No entries found for this name")

    st.markdown("---")

    category = st.selectbox("Category", list(CATEGORY_CONFIG.keys()))
    config = CATEGORY_CONFIG[category]
    dishes = category_data[category]

    # Dish selection
    dish_options = list(dishes.keys())
    dish_choice = st.selectbox("Select Dish", ["+ Add New Dish"] + dish_options)

    if dish_choice == "+ Add New Dish":
        new_dish = st.text_input("Enter New Dish Name")
        dish = new_dish
    else:
        dish = dish_choice

    # Info text
    st.info(f"Max varieties: {config['variety_limit']} | Contributors per dish: {config['min_people']}–{config['max_people']}")

    # Checks
    is_new_dish = dish not in dishes
    current_varieties = len(dishes)
    current_people = len(dishes[dish]) if dish in dishes else 0

    duplicate_name = any(e["name"] == name for e in st.session_state.entries)

    if duplicate_name:
        st.warning("You already have an entry. You can remove yourself and re-add.")

    if st.button("Submit", use_container_width=True):
        if not name or not dish:
            st.error("Fill all fields")
        elif duplicate_name:
            st.error("Duplicate name not allowed. Remove existing entry first.")
        elif is_new_dish and current_varieties >= config["variety_limit"]:
            st.error("Variety limit reached")
        elif not is_new_dish and current_people >= config["max_people"]:
            st.error("Dish already has max contributors")
        else:
            st.session_state.entries.append({
                "name": name,
                "category": category,
                "dish": dish
            })
            st.success("Added")
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
    total_people = len(st.session_state.entries)
    total_dishes = sum(len(d) for d in category_data.values())

    m1, m2 = st.columns(2)
    m1.metric("Total Contributors", total_people)
    m2.metric("Total Dishes", total_dishes)

    # Download buttons
    st.subheader("⬇️ Download Data")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, "potluck.csv", "text/csv")

    excel_file = "potluck.xlsx"
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as f:
        st.download_button("Download Excel", f, file_name=excel_file)
