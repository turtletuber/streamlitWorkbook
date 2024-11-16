import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Interactive Student Workbook",
    page_icon="📚",
    layout="wide"
)

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize session state
if "current_lesson" not in st.session_state:
    st.session_state.current_lesson = None
if "student_notes" not in st.session_state:
    st.session_state.student_notes = {}
if "student_progress" not in st.session_state:
    st.session_state.student_progress = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def load_lesson_plan(uploaded_file):
    """Load and parse the lesson plan JSON file"""
    try:
        content = json.load(uploaded_file)
        st.session_state.current_lesson = content
        initialize_progress_tracking(content)
        return True
    except Exception as e:
        st.error(f"Error loading lesson plan: {e}")
        return False

def initialize_progress_tracking(lesson_plan):
    """Initialize progress tracking for each section of the lesson"""
    if lesson_plan["content"]:
        sections = parse_lesson_sections(lesson_plan["content"])
        for section in sections.keys():
            if section not in st.session_state.student_progress:
                st.session_state.student_progress[section] = {
                    "completed": False,
                    "time_spent": 0,
                    "last_accessed": None
                }

def parse_lesson_sections(content):
    """Parse lesson content into sections"""
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if any(section in line for section in ["Overview:", "Learning Objectives:", "Required Materials:", 
                                             "Preparation Steps:", "Lesson Procedure:", 
                                             "Extensions and Modifications:", "Assessment Criteria:", 
                                             "Safety Considerations:", "Take-Home Connection:"]):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = line.strip()
            current_content = []
        elif current_section and line.strip():
            current_content.append(line.strip())
    
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def get_ai_help(question, context):
    """Get AI assistance for student questions"""
    prompt = f"""
    As a helpful teaching assistant, please help answer this student's question about their lesson.
    
    Lesson Context:
    {context}
    
    Student Question:
    {question}
    
    Please provide a clear, encouraging, and grade-appropriate response that helps the student understand 
    the concept better without simply giving away answers.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't process your question right now. Error: {str(e)}"

def display_student_workbook():
    """Display the interactive student workbook"""
    if not st.session_state.current_lesson:
        st.warning("Please upload a lesson plan to begin.")
        return

    lesson = st.session_state.current_lesson
    
    # Display lesson header
    st.title("📚 Student Workbook")
    st.subheader(f"{lesson['subject_area']} - {lesson['specific_topic']}")
    
    # Progress Overview
    with st.expander("📊 Your Progress", expanded=True):
        progress_df = pd.DataFrame([
            {
                "Section": section,
                "Status": "✅ Completed" if data["completed"] else "⏳ In Progress",
                "Time Spent (minutes)": data["time_spent"]
            }
            for section, data in st.session_state.student_progress.items()
        ])
        st.dataframe(progress_df, use_container_width=True)

    # Parse and display sections
    sections = parse_lesson_sections(lesson['content'])
    
    for section_title, content in sections.items():
        with st.expander(f"📝 {section_title}", expanded=True):
            # Display section content
            st.markdown(content)
            
            # Notes area
            notes_key = f"notes_{section_title}"
            if notes_key not in st.session_state.student_notes:
                st.session_state.student_notes[notes_key] = ""
            
            st.write("---")
            st.subheader("📝 Your Notes")
            notes = st.text_area(
                "Take notes here",
                value=st.session_state.student_notes[notes_key],
                key=notes_key,
                height=150
            )
            st.session_state.student_notes[notes_key] = notes
            
            # Questions for this section
            st.write("---")
            st.subheader("❓ Questions")
            question = st.text_input(
                "Ask a question about this section",
                key=f"question_{section_title}"
            )
            
            if st.button("Get Help", key=f"help_{section_title}"):
                if question:
                    response = get_ai_help(question, content)
                    st.session_state.chat_history.append({
                        "section": section_title,
                        "question": question,
                        "response": response,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.write("Response:", response)
            
            # Section completion tracking
            completed = st.checkbox(
                "Mark section as complete",
                value=st.session_state.student_progress[section_title]["completed"],
                key=f"complete_{section_title}"
            )
            if completed != st.session_state.student_progress[section_title]["completed"]:
                st.session_state.student_progress[section_title]["completed"] = completed
                st.session_state.student_progress[section_title]["last_accessed"] = datetime.now()

    # Question History
    with st.expander("📋 Question History", expanded=False):
        if st.session_state.chat_history:
            for entry in reversed(st.session_state.chat_history):
                st.write(f"**Section:** {entry['section']}")
                st.write(f"**Question:** {entry['question']}")
                st.write(f"**Response:** {entry['response']}")
                st.write(f"**Time:** {entry['timestamp']}")
                st.write("---")
        else:
            st.write("No questions asked yet.")

    # Export functionality
    if st.button("Export Progress and Notes"):
        export_data = {
            "lesson_info": {
                "subject": lesson["subject_area"],
                "topic": lesson["specific_topic"],
                "grade_level": lesson["grade_level"]
            },
            "progress": st.session_state.student_progress,
            "notes": st.session_state.student_notes,
            "question_history": st.session_state.chat_history
        }
        
        st.download_button(
            label="Download Progress Report",
            data=json.dumps(export_data, indent=2),
            file_name=f"workbook_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def main():
    st.sidebar.title("📚 Student Workbook")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Lesson Plan",
        type=["json"],
        help="Upload the JSON lesson plan file"
    )
    
    if uploaded_file:
        if load_lesson_plan(uploaded_file):
            display_student_workbook()
    else:
        st.write("Welcome to your interactive workbook! Please upload a lesson plan to begin.")
        st.write("""
        ### Features:
        - 📝 Take notes for each section
        - ❓ Ask questions and get AI assistance
        - ✅ Track your progress
        - 📊 Export your work and progress
        """)

if __name__ == "__main__":
    main()
