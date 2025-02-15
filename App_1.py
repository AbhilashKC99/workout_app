import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# Function to load exercise and save CSV files
def load_csv(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame

# Function to get the pending exercises for selected body parts
def get_pending_exercises(selected_bodyparts, exercise_list, save_csv, now_woy):
    pending_exercises = {}
    for bodypart in selected_bodyparts:
        exercises = exercise_list[exercise_list["Bodypart"] == bodypart]["Exercises"].values[0]
        
        # Track pending exercises for this body part
        pending = []
        for exercise in exercises:
            completed = save_csv[
                (save_csv["Exercise"] == exercise) & 
                (save_csv["WOY"] == now_woy)
            ]
            if completed.empty:
                pending.append(exercise)
        
        if pending:
            pending_exercises[bodypart] = pending
    
    return pending_exercises

# Function to save exercise data
def save_exercise(new_row, stat_save_path):
    try:
        stat_save = load_csv(stat_save_path)
        if stat_save.empty:  # If file is empty, create columns
            stat_save = pd.DataFrame(columns=["WOY", "WOD", "Date", "Exercise", "Reps", "Weight"])
        
        new_row_df = pd.DataFrame([new_row])
        stat_save = pd.concat([stat_save, new_row_df], ignore_index=True)
        
        stat_save.to_csv(stat_save_path, index=False)
        st.success(f"{new_row['Exercise']} logged successfully!")
        return True
    except Exception as e:
        st.error(f"Error saving exercise: {e}")
        return False

# Function to get the current week and day of the week
def get_current_date_info(date_df, now):
    now_woy = find_match(date_df, 'date', now, 'week_of_year')
    now_dow = find_match(date_df, 'date', now, 'day_of_week')
    return now_woy, now_dow

# Function to find matching row in dataframe based on conditions
def find_match(df, col_to_check, value_to_match, col_to_return):
    match = df[df[col_to_check] == value_to_match]
    if not match.empty:
        return match[col_to_return].iloc[0]
    return None

# Function to display progress of completed exercises for the current week
def display_week_progress(save_csv, now_woy):
    completed_exercises = save_csv[save_csv["WOY"] == now_woy]
    if completed_exercises.empty:
        st.info("Begin your week! Get started with your workout routine.")
    else:
        exercises_completed = completed_exercises.groupby("WOD")["Exercise"].apply(list)
        st.subheader("Exercises Completed This Week:")
        for day, exercises in exercises_completed.items():
            st.write(f"Day {day}: {', '.join(exercises)}")

# Main Streamlit code
def main():
    st.set_page_config(page_title="Workout Tracker", page_icon="🏋️‍♂️")
    
    # Load exercise list and save CSV
    exercise_list = load_csv("/Users/abhilash_mac/Documents/Data Projects/Streamlit/App_1/exercises.csv")
    save_csv = load_csv("/Users/abhilash_mac/Documents/Data Projects/Streamlit/App_1/stat_save.csv")
    
    # Clean column names
    save_csv.columns = save_csv.columns.str.strip()
    exercise_list.columns = exercise_list.columns.str.strip()

    # Split exercises into lists
    exercise_list["Exercises"] = exercise_list["Exercises"].apply(lambda x: [e.strip() for e in x.split(",")])

    # Set timezone to EST
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    now = now.strftime('%Y-%m-%d')  # Current date in EST format
    
    # Generate a date range and week of the year (WOY)
    dates = pd.date_range(start='2025-02-01', end='2025-02-28')
    date_df = pd.DataFrame({'date': dates})
    date_df['day_of_week'] = date_df['date'].dt.dayofweek
    date_df['week_of_year'] = date_df['date'].dt.isocalendar().week

    now_woy, now_dow = get_current_date_info(date_df, now)

    # Display exercises completed for the current week
    display_week_progress(save_csv, now_woy)

    # Bodypart selection
    select_bp = exercise_list["Bodypart"].unique()

    # Get pending exercises for selected body parts
    pending_exercises = get_pending_exercises(select_bp, exercise_list, save_csv, now_woy)

    # Filter body parts that still have pending exercises
    available_bodyparts = [bodypart for bodypart in select_bp if bodypart in pending_exercises]

    st.subheader("Select Body Parts to Train:")
    selected_bodyparts = [item for item in available_bodyparts if st.checkbox(item)]

    if "pending_exercises" not in st.session_state:
        st.session_state.pending_exercises = []

    # Button to show pending exercises
    if st.button("Give me pending exercises"):
        if selected_bodyparts:
            pending_exercises = get_pending_exercises(selected_bodyparts, exercise_list, save_csv, now_woy)
            st.session_state.pending_exercises = [exercise for exercises in pending_exercises.values() for exercise in exercises]
            
            if st.session_state.pending_exercises:
                st.success("Pending Exercises:")
                st.write(st.session_state.pending_exercises)
            else:
                st.info("No pending exercises for the selected body parts.")
        else:
            st.warning("Please select at least one body part.")

    # Log exercise details if there are pending exercises
    if st.session_state.pending_exercises:
        st.subheader("Log Your Exercise Details:")
        
        selected_exercise = st.selectbox("Choose an exercise:", st.session_state.pending_exercises)
        reps = st.number_input("Enter Reps:", min_value=1, step=1, value=6)  # Default value 6
        weight = st.text_input("Enter Weight (e.g., 25 lbs):", value="25 lbs")  # Default value 25 lbs
        
        if st.button("Save Exercise"):
            if selected_exercise and reps > 0 and weight:
                new_row = {
                    "WOY": now_woy,
                    "WOD": now_dow,
                    "Date": now,
                    "Exercise": selected_exercise,
                    "Reps": reps,
                    "Weight": weight
                }

                stat_save_path = "/Users/abhilash_mac/Documents/Data Projects/Streamlit/App_1/stat_save.csv"
                if save_exercise(new_row, stat_save_path):
                    # Remove the logged exercise from the pending list
                    st.session_state.pending_exercises.remove(selected_exercise)
                    st.rerun()  # Refresh the UI after saving
            else:
                st.error("Please fill all fields before saving.")

if __name__ == "__main__":
    main()
