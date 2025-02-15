import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Function to load exercise list CSV
def load_exercise_list(file_path):
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        df["Exercises"] = df["Exercises"].apply(lambda x: [e.strip() for e in x.split(",")])
        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return pd.DataFrame()  # Return an empty DataFrame

# Function to distribute exercises over 5 days
def distribute_exercises(exercise_list):
    # Flatten the list of all exercises
    all_exercises = []
    for exercises in exercise_list["Exercises"]:
        all_exercises.extend(exercises)

    # Get current week of the year
    now = datetime.now()
    current_week = now.isocalendar().week

    # Reset completed exercises at the start of each week or on refresh
    if "previous_week" not in st.session_state or st.session_state.previous_week != current_week:
        st.session_state.previous_week = current_week
        st.session_state.completed_exercises = []

    # Filter out exercises completed last week
    available_exercises = [ex for ex in all_exercises if ex not in st.session_state.completed_exercises]

    # If no exercises are available, reset and start fresh
    if not available_exercises:
        available_exercises = all_exercises
        st.session_state.completed_exercises = []

    # Shuffle exercises with a seed to ensure variation each week
    random.seed(current_week)
    random.shuffle(available_exercises)

    # Distribute exercises across 5 days
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    workout_plan = {day: [] for day in days}

    # Calculate the number of exercises per day
    num_days = len(days)
    exercises_per_day = len(available_exercises) // num_days
    extra_exercises = len(available_exercises) % num_days

    # Assign exercises to each day
    idx = 0
    for day in days:
        num_exercises = exercises_per_day + (1 if extra_exercises > 0 else 0)
        workout_plan[day] = available_exercises[idx:idx + num_exercises]
        idx += num_exercises
        extra_exercises -= 1
    
    # Save the completed exercises to avoid repetition next week
    st.session_state.completed_exercises.extend(available_exercises)

    return workout_plan

def main():
    st.title("Weekly Workout Suggestions 💪")

    # Load exercise list
    exercise_list_path = "/Users/abhilash_mac/Documents/Data Projects/Streamlit/App_1/exercises.csv"
    exercise_list = load_exercise_list(exercise_list_path)
    
    if exercise_list.empty:
        st.info("No exercises found. Please check the CSV file.")
        return

    # Generate workout plan
    workout_plan = distribute_exercises(exercise_list)

    # Display the workout plan
    st.subheader("Your Suggested Workout Plan for the Week:")
    for day, exercises in workout_plan.items():
        st.markdown(f"### {day}")
        if exercises:
            for ex in exercises:
                st.write(f"- {ex}")
        else:
            st.write("Rest Day!")

    # Refresh Button to regenerate workout plan
    if st.button("🔄 Refresh Workout Plan"):
        # Clear completed exercises to reshuffle
        st.session_state.completed_exercises = []
        st.rerun()

if __name__ == "__main__":
    main()
