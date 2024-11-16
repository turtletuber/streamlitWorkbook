import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Project Workbook",
    page_icon="🚀",
    layout="wide"
)

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize session state
if "project_data" not in st.session_state:
    st.session_state.project_data = None
if "project_journal" not in st.session_state:
    st.session_state.project_journal = []
if "research_notes" not in st.session_state:
    st.session_state.research_notes = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "project_milestones" not in st.session_state:
    st.session_state.project_milestones = []
if "reflection_log" not in st.session_state:
    st.session_state.reflection_log = []

def load_project_plan(uploaded_file):
    """Load and parse the project plan JSON file"""
    try:
        content = json.load(uploaded_file)
        st.session_state.project_data = content
        initialize_project_structure(content)
        return True
    except Exception as e:
        st.error(f"Error loading project plan: {e}")
        return False

def initialize_project_structure(project_data):
    """Initialize project structure and milestones"""
    # Extract project milestones from the lesson procedure
    if "content" in project_data:
        sections = parse_lesson_sections(project_data["content"])
        if "Lesson Procedure:" in sections:
            procedure = sections["Lesson Procedure:"]
            steps = [step.strip() for step in procedure.split('\n') if step.strip()]
            st.session_state.project_milestones = [
                {"step": step, "completed": False, "evidence": "", "reflection": ""}
                for step in steps
            ]

def get_ai_help(question, context):
    """Get AI assistance for student questions"""
    prompt = f"""
    As a helpful project mentor, please help answer this student's question about their project work.
    
    Project Context:
    {context}
    
    Student Question:
    {question}
    
    Please provide a constructive response that:
    1. Guides the student's thinking without giving direct answers
    2. Suggests possible approaches or resources
    3. Encourages critical thinking and creativity
    4. Relates to real-world applications where possible
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-002')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't process your question right now. Error: {str(e)}"

def display_project_workbook():
    """Display the interactive project workbook"""
    if not st.session_state.project_data:
        st.warning("Please upload your project plan to begin.")
        return

    project = st.session_state.project_data
    
    # Project Overview
    st.title("🚀 My Project Workbook")
    st.subheader(f"{project['subject_area']} - {project['specific_topic']}")

    # Project Dashboard
    col1, col2, col3 = st.columns(3)
    with col1:
        completed_steps = len([m for m in st.session_state.project_milestones if m["completed"]])
        total_steps = len(st.session_state.project_milestones)
        st.metric("Project Progress", f"{completed_steps}/{total_steps} Steps")
    
    with col2:
        st.metric("Project Timeline", project['delivery_timeline'])
    
    with col3:
        st.metric("Research Notes", f"{len(st.session_state.research_notes)} Entries")

    # Project Goals and Success Criteria
    with st.expander("📋 Project Goals and Success Criteria", expanded=True):
        st.markdown(f"""
        **Project Objectives:**
        {project['objectives']}
        
        **What you'll create:**
        {parse_lesson_sections(project['content']).get('Overview:', 'Project details loading...')}
        """)

    # Project Journal
    st.header("📔 Project Journal")
    
    # Add new journal entry
    with st.expander("✏️ Add Journal Entry", expanded=True):
        entry_date = st.date_input("Date", datetime.now())
        entry_type = st.selectbox(
            "Entry Type",
            ["Progress Update", "Challenge Faced", "Breakthrough", "Question", "Research Notes"]
        )
        entry_content = st.text_area("What did you work on today?")
        next_steps = st.text_area("What are your next steps?")
        
        if st.button("Save Entry"):
            st.session_state.project_journal.append({
                "date": entry_date.strftime("%Y-%m-%d"),
                "type": entry_type,
                "content": entry_content,
                "next_steps": next_steps
            })
            st.success("Journal entry saved!")

    # Project Milestones Tracker
    st.header("🎯 Project Milestones")
    for idx, milestone in enumerate(st.session_state.project_milestones):
        with st.expander(f"Step {idx + 1}: {milestone['step']}", expanded=not milestone['completed']):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Evidence of work
                milestone['evidence'] = st.text_area(
                    "Document your work for this step",
                    value=milestone['evidence'],
                    key=f"evidence_{idx}",
                    height=100
                )
                
                # Reflection
                milestone['reflection'] = st.text_area(
                    "Reflect on this step (What worked? What did you learn? What would you do differently?)",
                    value=milestone['reflection'],
                    key=f"reflection_{idx}",
                    height=100
                )
                
                # Questions/Help
                question = st.text_input("Need help? Ask a question:", key=f"q_{idx}")
                if st.button("Get Help", key=f"help_{idx}"):
                    if question:
                        response = get_ai_help(question, milestone['step'])
                        st.session_state.chat_history.append({
                            "step": milestone['step'],
                            "question": question,
                            "response": response,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        st.write("Response:", response)
            
            with col2:
                # Completion status
                milestone['completed'] = st.checkbox(
                    "Mark as complete",
                    value=milestone['completed'],
                    key=f"complete_{idx}"
                )

    # Research and Resources
    st.header("📚 Research Notes")
    with st.expander("Add Research Notes", expanded=False):
        source = st.text_input("Source/Reference")
        notes = st.text_area("Key Points and Notes")
        if st.button("Save Research Notes"):
            if source:
                st.session_state.research_notes[source] = notes
                st.success("Research notes saved!")

    # Project Reflection Log
    st.header("💭 Overall Project Reflection")
    if st.button("Add Reflection"):
        reflection = st.text_area(
            "Reflect on your project progress, challenges, and learning",
            height=200
        )
        if reflection:
            st.session_state.reflection_log.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "reflection": reflection
            })

    # Export Project Work
    if st.button("Export Project Work"):
        export_data = {
            "project_info": project,
            "journal_entries": st.session_state.project_journal,
            "milestones": st.session_state.project_milestones,
            "research_notes": st.session_state.research_notes,
            "reflection_log": st.session_state.reflection_log,
            "questions_and_help": st.session_state.chat_history
        }
        
        st.download_button(
            label="Download Project Portfolio",
            data=json.dumps(export_data, indent=2),
            file_name=f"project_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

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

def main():
    st.sidebar.title("🚀 Project Workbook")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload Project Plan",
        type=["json"],
        help="Upload your project plan file"
    )
    
    if uploaded_file:
        if load_project_plan(uploaded_file):
            display_project_workbook()
    else:
        st.write("Welcome to your project workbook! Upload your project plan to begin.")
        st.write("""
        ### What you can do here:
        - 📔 Keep a project journal
        - 🎯 Track your project milestones
        - 📚 Take research notes
        - ❓ Get help when you need it
        - 💭 Reflect on your learning
        - 📊 Export your project portfolio
        
        This workbook helps you document your project journey, from initial ideas to final reflection!
        """)

if __name__ == "__main__":
    main()
