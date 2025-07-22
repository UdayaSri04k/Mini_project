import streamlit as st
import pandas as pd
import random
import copy
import io

# Upload and load the Excel file
uploaded_file = st.file_uploader("Upload the timetable Excel file", type=["xlsx"])

# Check if a file was uploaded
if uploaded_file:
    
    # Load data for each section from separate sheets in the uploaded Excel file
    data_section1 = pd.read_excel(uploaded_file, sheet_name='section1')
    data_section2 = pd.read_excel(uploaded_file, sheet_name='section2')
    data_section3 = pd.read_excel(uploaded_file, sheet_name='section3')
    data_section4 = pd.read_excel(uploaded_file, sheet_name='section4')

    # Global list to store labs from all sections to avoid duplication
    all_labs = []

    # Extracts subjects, their frequencies, labs, and faculty assignments for a given section
    def extract_data(data):
        subjects = data['Subjects'].dropna().tolist()
        subjects_frequency = dict(zip(data['Subjects'].dropna(), data['Frequency'].dropna()))
        labs = data['Labs'].dropna().tolist()
        all_labs.extend(labs)  # Append extracted labs to the global list 
        faculty = dict(zip(data['Subject/Lab'], data['Faculty']))
        return subjects, subjects_frequency, labs, faculty

    # Extract data for all four sections
    subjects1, subjects_frequency1, labs1, faculty_section1 = extract_data(data_section1)
    subjects2, subjects_frequency2, labs2, faculty_section2 = extract_data(data_section2)
    subjects3, subjects_frequency3, labs3, faculty_section3 = extract_data(data_section3)
    subjects4, subjects_frequency4, labs4, faculty_section4 = extract_data(data_section4)

    # Remove duplicates and assign the result to 'labs'
    labs = list(set(all_labs))

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    periods = ['Period 1', 'Period 2', 'Period 3', 'Period 4', 'Lunch Break', 'Period 5', 'Period 6', 'Period 7']

    def create_empty_timetable():
        return {day: [None] * 7 for day in days}  # 7 slots (excluding Lunch Break)

    # Create empty timetables for all four sections
    timetable_section_1 = create_empty_timetable()
    timetable_section_2 = create_empty_timetable()
    timetable_section_3 = create_empty_timetable()
    timetable_section_4 = create_empty_timetable()

    # Assigns static labs and PCS periods from Excel sheet
    def assign_static_labs(timetable, static_assignments):
        for _, row in static_assignments.iterrows():
            day = row['Days']
            if day not in days:
                continue  # Skip invalid day entries
            for period in range(1, 8):  # Periods 1 to 7 (excluding Lunch Break)
                period_col = f'Period {period}'
                subject = row.get(period_col, None)
                if pd.notna(subject):  # Assign only if subject is not NaN
                    timetable[day][period - 1] = subject  # Adjusting for 0-index

    # Assign static labs and PCS for each section using data from Excel
    assign_static_labs(timetable_section_1, data_section1)
    assign_static_labs(timetable_section_2, data_section2)
    assign_static_labs(timetable_section_3, data_section3)
    assign_static_labs(timetable_section_4, data_section4)

    # Function to check for collision
    def has_collision(timetable, day, period_range):
        return any(timetable[day][period] is not None for period in period_range)

    # Function to check if a subject exceeds daily period limit
    def exceeds_daily_limit(timetable, day, subject):
        matching_elements = [x for x in labs if x in timetable[day]]
        if matching_elements:
            return timetable[day].count(subject) >= 1
        else:
            return timetable[day].count(subject) >= 2

    # Function to assign Library and Sports (once a week)
    def assign_others(timetable):
        library_assigned = False
        sports_assigned = False
        for day in random.sample(days, len(days)):
            if library_assigned and sports_assigned:
                break
            if not library_assigned:
                for period in [3, 6]:  # Library can be assigned in 4th or 7th period
                    if not has_collision(timetable, day, [period]):
                        timetable[day][period] = 'Library'
                        library_assigned = True
                        break
            if not sports_assigned:
                if not has_collision(timetable, day, [6]):
                    timetable[day][6] = 'Sports'
                    sports_assigned = True

    # Assign subjects for sections 1 & 2
    def assign_subjects_1(timetable_1, timetable_2):
        subject_counts = {subject: 0 for subject in subjects1}
        temp_timetable = copy.deepcopy(timetable_1)
        temp_subs_count = subject_counts.copy()
        for day in days:
            for period in range(len(periods) - 1):
                if temp_timetable[day][period] is not None:
                    continue
                attempts = 0
                temp_subs = [sub for sub in temp_subs_count if temp_subs_count[sub] < subjects_frequency1[sub]]
                while attempts < 8:
                    if not temp_subs:
                        break
                    attempts += 1
                    sub = random.choice(temp_subs)
                    if (timetable_2[day][period] is not None and
                        faculty_section2[timetable_2[day][period]] == faculty_section1[sub]):
                        continue
                    if temp_timetable[day][period] is None and not exceeds_daily_limit(temp_timetable, day, sub):
                        temp_timetable[day][period] = sub
                        temp_subs_count[sub] += 1
                        break
                if attempts == 8:
                    return assign_subjects_1(timetable_1, timetable_2)
        return temp_timetable

    # Assign subjects for sections 3 & 4
    def assign_subjects_2(timetable_3, timetable_4):
        subject_counts = {subject: 0 for subject in subjects3}
        temp_timetable = copy.deepcopy(timetable_3)
        temp_subs_count = subject_counts.copy()
        for day in days:
            for period in range(len(periods) - 1):
                if temp_timetable[day][period] is not None:
                    continue
                attempts = 0
                temp_subs = [sub for sub in temp_subs_count if temp_subs_count[sub] < subjects_frequency3[sub]]
                while attempts < 8:
                    if not temp_subs:
                        break
                    attempts += 1
                    sub = random.choice(temp_subs)
                    if (timetable_4[day][period] is not None and
                        timetable_4[day][period] in faculty_section4 and
                        faculty_section4[timetable_4[day][period]] == faculty_section3[sub]):
                        continue
                    if temp_timetable[day][period] is None and not exceeds_daily_limit(temp_timetable, day, sub):
                        temp_timetable[day][period] = sub
                        temp_subs_count[sub] += 1
                        break
                if attempts == 8:
                    return assign_subjects_2(timetable_3, timetable_4)
        return temp_timetable
    
    # Inserts 'Lunch Break' into the 4th position for every day
    def insert_lunch_break(timetable):
        for day in days:
            timetable[day].insert(4, "Lunch Break")  # Lunch Break at 4th index

    # Assign Library and Sports for all sections
    assign_others(timetable_section_1)
    assign_others(timetable_section_2)
    assign_others(timetable_section_3)
    assign_others(timetable_section_4)

    # Assign subjects for each section
    timetable_section_1 = assign_subjects_1(timetable_section_1, timetable_section_2)
    timetable_section_2 = assign_subjects_1(timetable_section_2, timetable_section_1)
    timetable_section_3 = assign_subjects_2(timetable_section_3, timetable_section_4)
    timetable_section_4 = assign_subjects_2(timetable_section_4, timetable_section_3)

    # Insert Lunch Breaks into each timetable
    insert_lunch_break(timetable_section_1)
    insert_lunch_break(timetable_section_2)
    insert_lunch_break(timetable_section_3)
    insert_lunch_break(timetable_section_4)

    timetable_df_section_1 = pd.DataFrame(timetable_section_1, index=periods)
    timetable_df_section_2 = pd.DataFrame(timetable_section_2, index=periods)
    timetable_df_section_3 = pd.DataFrame(timetable_section_3, index=periods)
    timetable_df_section_4 = pd.DataFrame(timetable_section_4, index=periods)

    st.write("### Time Table for Section 1")
    st.dataframe(timetable_df_section_1.transpose())

    st.write("### Time Table for Section 2")
    st.dataframe(timetable_df_section_2.transpose())

    st.write("### Time Table for Section 3")
    st.dataframe(timetable_df_section_3.transpose())

    st.write("### Time Table for Section 4")
    st.dataframe(timetable_df_section_4.transpose())