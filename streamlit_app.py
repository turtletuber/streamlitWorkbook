import streamlit as st
import google.generativeai as genai
import json
import os

# Page configuration
st.set_page_config(
    page_title="Student Interactive Workbook",
    page_icon="📘",
    layout="wide"
)

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize session state
if "student_notes" not in st.session_state:
    st.session_state.student_notes = {}
if "student_answers" not in st.session_state:
    st.session_state.student_answers = {}
if "lesson_content" not in st.session_state:
    st.session_state.lesson_content = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def load_lesson_plan(file):
    """Load lesson plan JSON file"""
    try:
        content = json.load(file)
        return content
    except Exception as e:
        st.error(f"Error loading lesson plan: {e}")
        return None

def parse_lesson_sections(content):
    """Parse lesson content into sections"""
    sections = {}
    current_section = None
    current_content = []
    
    if not content:
        return sections
        
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
    
    # Add the last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def ai_respond(user_input):
    """Get AI response to student's question"""
    prompt = f"""
    The student asked: "{user_input}"
    Provide a helpful, age-appropriate response to assist the student in understanding the lesson material.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error getting AI response: {e}")
        return "I'm sorry, I couldn't process your question."

def main():
    st.title("📘 Student Interactive Workbook")
    st.write("Follow along with your lesson, take notes, and interact with the AI assistant.")

    # File uploader to load lesson plan
    uploaded_file = st.file_uploader("Upload Lesson Plan JSON File", type="json")

    if uploaded_file is not None:
        lesson_plan = load_lesson_plan(uploaded_file)
        if lesson_plan:
            st.session_state.lesson_content = lesson_plan
            st.success("Lesson plan loaded successfully!")
            st.experimental_rerun()

    if st.session_state.lesson_content:
        lesson_data = st.session_state.lesson_content

        # Display lesson metadata
        st.header(f"Lesson: {lesson_data.get('specific_topic', 'N/A')}")
        st.markdown(f"""
        **Grade Level:** {lesson_data.get('grade_level', 'N/A')}  
        **Subject:** {lesson_data.get('subject_area', 'N/A')}  
        **Delivery Timeline:** {lesson_data.get('delivery_timeline', 'N/A')}
        """)
        
        # Parse lesson sections
        sections = parse_lesson_sections(lesson_data.get('content', ''))

        # Display sections for students to interact with
        for section, content in sections.items():
            if section == "Learning Objectives:":
                st.subheader(section.replace(":", ""))
                st.markdown(content)
                continue  # No student interaction needed here

            with st.expander(f"🔍 {section.replace(':', '')}", expanded=True):
                st.markdown(content)

                # Student Notes
                note_key = f"note_{section}"
                st.text_area(
                    "Your Notes:",
                    value=st.session_state.student_notes.get(note_key, ""),
                    key=note_key,
                    height=100
                )
                st.session_state.student_notes[note_key] = st.session_state[note_key]

                # Student Answers (if section contains questions)
                if "?" in content:
                    answer_key = f"answer_{section}"
                    st.text_input(
                        "Your Answer:",
                        value=st.session_state.student_answers.get(answer_key, ""),
                        key=answer_key
                    )
                    st.session_state.student_answers[answer_key] = st.session_state[answer_key]

        # AI Assistant Chat
        st.header("🤖 Ask the AI Assistant")
        user_question = st.text_input("Have a question about the lesson?")
        if st.button("Ask"):
            if user_question:
                with st.spinner("AI Assistant is thinking..."):
                    response = ai_respond(user_question)
                    st.session_state.chat_history.append({"user": user_question, "ai": response})
                    st.success("AI Assistant has responded!")
                    st.experimental_rerun()
            else:
                st.warning("Please enter a question.")

        # Display chat history
        if st.session_state.chat_history:
            st.subheader("Chat History")
            for chat in st.session_state.chat_history:
                st.markdown(f"**You:** {chat['user']}")
                st.markdown(f"**AI Assistant:** {chat['ai']}")
                st.write("---")

        # Save Notes and Answers
        if st.button("Save Your Progress"):
            student_data = {
                "notes": st.session_state.student_notes,
                "answers": st.session_state.student_answers,
                "chat_history": st.session_state.chat_history
            }
            file_name = f"student_progress_{lesson_data.get('specific_topic', 'lesson')}.json"
            with open(file_name, 'w') as f:
                json.dump(student_data, f, indent=2)
            st.success(f"Your progress has been saved to {file_name}")

        # Download Student Progress
        st.download_button(
            label="Download Your Progress",
            data=json.dumps({
                "notes": st.session_state.student_notes,
                "answers": st.session_state.student_answers,
                "chat_history": st.session_state.chat_history
            }, indent=2),
            file_name=f"student_progress_{lesson_data.get('specific_topic', 'lesson')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    main()
