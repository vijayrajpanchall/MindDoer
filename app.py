import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import json

# Configure Streamlit page
st.set_page_config(
    page_title="AI Life Coach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .task-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        color: #2c3e50;
    }
    
    .high-priority {
        border-left-color: #e74c3c;
    }
    
    .medium-priority {
        border-left-color: #f39c12;
    }
    
    .low-priority {
        border-left-color: #2ecc71;
    }
    
    .urgent-priority {
        border-left-color: #8e44ad;
    }
    
    .user-task {
        background: #e8f5e8;
        border-left-color: #27ae60;
    }
    
    .ai-task {
        background: #e8f4fd;
        border-left-color: #3498db;
    }
    
    .stats-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .motivation-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'completed_tasks' not in st.session_state:
    st.session_state.completed_tasks = []
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'daily_context' not in st.session_state:
    st.session_state.daily_context = {}
if 'goals' not in st.session_state:
    st.session_state.goals = []
if 'show_setup' not in st.session_state:
    st.session_state.show_setup = True

# Priority and energy mappings
PRIORITY_COLORS = {
    "Low": "#2ecc71",
    "Medium": "#f39c12", 
    "High": "#e74c3c",
    "Urgent": "#8e44ad"
}

ENERGY_LEVELS = ["Exhausted", "Low", "Moderate", "High", "Peak"]
MOOD_LEVELS = ["Very Low", "Low", "Neutral", "Good", "Excellent"]
CATEGORIES = ["Work", "Personal", "Health", "Learning", "Social"]

# Helper functions
def create_task(title, description, priority, estimated_time, category, energy_required, user_created=True):
    """Create a new task dictionary"""
    return {
        'id': str(uuid.uuid4()),
        'title': title,
        'description': description,
        'priority': priority,
        'estimated_time': estimated_time,
        'category': category,
        'energy_required': energy_required,
        'status': 'Pending',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'user_created': user_created,
        'completed_at': None
    }

def display_task_card(task, index):
    """Display a task as a card"""
    priority_class = f"{task['priority'].lower()}-priority"
    task_type_class = "user-task" if task['user_created'] else "ai-task"
    
    task_icon = "👤" if task['user_created'] else "🤖"
    priority_icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴", "Urgent": "🟣"}[task['priority']]
    
    with st.container():
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        
        with col1:
            if st.button("✅", key=f"complete_{task['id']}", help="Mark as complete"):
                complete_task(task['id'])
                st.rerun()
        
        with col2:
            st.markdown(f"""
                <div class="task-card {priority_class} {task_type_class}">
                    <h4 style="color: #2c3e50;">{task_icon} {task['title']} {priority_icon}</h4>
                    <p style="color: #34495e;"><strong>Description:</strong> {task['description']}</p>
                    <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #34495e;">
                        <span>⏱️ {task['estimated_time']} min</span>
                        <span>⚡ {task['energy_required']}</span>
                        <span>📂 {task['category']}</span>
                        <span>📊 {task['priority']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                delete_task(task['id'])
                st.rerun()

def complete_task(task_id):
    """Mark a task as completed"""
    for i, task in enumerate(st.session_state.tasks):
        if task['id'] == task_id:
            task['status'] = 'Completed'
            task['completed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            completed_task = st.session_state.tasks.pop(i)
            st.session_state.completed_tasks.append(completed_task)
            break

def delete_task(task_id):
    """Delete a task"""
    st.session_state.tasks = [task for task in st.session_state.tasks if task['id'] != task_id]

def generate_ai_suggestions():
    """Generate sample AI task suggestions based on user context"""
    suggestions = []
    
    # Get user context
    mood = st.session_state.daily_context.get('mood', 'Neutral')
    energy = st.session_state.daily_context.get('energy', 'Moderate')
    stress = st.session_state.daily_context.get('stress_level', 5)
    
    # Wellness suggestions based on stress
    if stress >= 7:
        suggestions.append(create_task(
            "Stress Relief Activity",
            "Take 15 minutes for deep breathing, meditation, or a short walk",
            "High", 15, "Health", "Low", False
        ))
    
    # Energy-based suggestions
    if energy in ["High", "Peak"]:
        suggestions.append(create_task(
            "Tackle Challenging Project",
            "Work on your most important but difficult task while energy is high",
            "High", 60, "Work", "High", False
        ))
    elif energy in ["Exhausted", "Low"]:
        suggestions.append(create_task(
            "Gentle Self-Care",
            "Do something nurturing - read, listen to music, or organize",
            "Medium", 30, "Personal", "Low", False
        ))
    
    # Goal-based suggestions
    for goal in st.session_state.goals[:2]:  # Max 2 goal-based tasks
        suggestions.append(create_task(
            f"Progress on: {goal[:25]}...",
            f"Take a concrete step towards: {goal}",
            "Medium", 45, "Personal", "Moderate", False
        ))
    
    # Mood-based suggestions
    if mood in ["Very Low", "Low"]:
        suggestions.append(create_task(
            "Connect with Someone",
            "Call a friend, family member, or write in a journal",
            "High", 20, "Social", "Low", False
        ))
    
    return suggestions

# Main App Layout
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Personal Life Coach</h1>
        <p>Your intelligent companion for productivity and well-being</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for user setup and context
    with st.sidebar:
        st.header("🛠️ Setup & Context")
        
        # User Profile Section
        with st.expander("👤 User Profile", expanded=st.session_state.show_setup):
            name = st.text_input("Name", value=st.session_state.user_profile.get('name', ''), key="name_input")
            motivation_style = st.selectbox(
                "Motivation Style", 
                ["Encouraging", "Direct", "Analytical"],
                index=0 if not st.session_state.user_profile.get('motivation_style') else 
                      ["Encouraging", "Direct", "Analytical"].index(st.session_state.user_profile.get('motivation_style'))
            )
            
            if st.button("Save Profile"):
                st.session_state.user_profile = {
                    'name': name,
                    'motivation_style': motivation_style
                }
                st.success("Profile saved!")
        
        # Daily Context Section
        with st.expander("📊 Today's Context", expanded=st.session_state.show_setup):
            mood = st.select_slider("Mood Level", MOOD_LEVELS, value=st.session_state.daily_context.get('mood', 'Neutral'))
            energy = st.select_slider("Energy Level", ENERGY_LEVELS, value=st.session_state.daily_context.get('energy', 'Moderate'))
            stress_level = st.slider("Stress Level (1-10)", 1, 10, st.session_state.daily_context.get('stress_level', 5))
            available_hours = st.number_input("Available Hours Today", 1, 12, st.session_state.daily_context.get('available_hours', 6))
            
            if st.button("Update Context"):
                st.session_state.daily_context = {
                    'mood': mood,
                    'energy': energy,
                    'stress_level': stress_level,
                    'available_hours': available_hours,
                    'date': datetime.now().strftime("%Y-%m-%d")
                }
                st.success("Context updated!")
        
        # Goals Section
        with st.expander("🎯 Your Goals"):
            new_goal = st.text_input("Add a new goal")
            if st.button("Add Goal") and new_goal:
                st.session_state.goals.append(new_goal)
                st.success(f"Goal added: {new_goal}")
            
            if st.session_state.goals:
                st.write("**Current Goals:**")
                for i, goal in enumerate(st.session_state.goals):
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        st.write(f"• {goal}")
                    with col2:
                        if st.button("🗑️", key=f"delete_goal_{i}"):
                            st.session_state.goals.pop(i)
                            st.rerun()
        
        # Quick Actions
        st.header("⚡ Quick Actions")
        if st.button("🤖 Get AI Suggestions", type="primary"):
            suggestions = generate_ai_suggestions()
            for suggestion in suggestions:
                st.session_state.tasks.append(suggestion)
            st.success(f"Added {len(suggestions)} AI suggestions!")
            st.rerun()
        
        if st.button("🔄 Clear All Tasks"):
            st.session_state.tasks = []
            st.session_state.completed_tasks = []
            st.success("All tasks cleared!")
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Task Management Section
        st.header("📋 Task Management")
        
        # Add new task form
        with st.expander("➕ Add New Task", expanded=False):
            with st.form("add_task_form"):
                task_title = st.text_input("Task Title*")
                task_desc = st.text_area("Description")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    task_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
                with col_b:
                    task_time = st.number_input("Time (minutes)", 5, 300, 30)
                with col_c:
                    task_category = st.selectbox("Category", CATEGORIES)
                
                task_energy = st.selectbox("Energy Required", ENERGY_LEVELS[1:4])  # Low to High
                
                if st.form_submit_button("Add Task", type="primary"):
                    if task_title:
                        new_task = create_task(
                            task_title, task_desc or task_title, task_priority,
                            task_time, task_category, task_energy, True
                        )
                        st.session_state.tasks.append(new_task)
                        st.success(f"Task '{task_title}' added!")
                        st.rerun()
                    else:
                        st.error("Please enter a task title!")
        
        # Current Tasks
        st.subheader("📝 Today's Tasks")
        if st.session_state.tasks:
            # Filter and sort options
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            with col_filter1:
                priority_filter = st.multiselect("Filter by Priority", ["Low", "Medium", "High", "Urgent"], key="priority_filter")
            with col_filter2:
                category_filter = st.multiselect("Filter by Category", CATEGORIES, key="category_filter")
            with col_filter3:
                sort_by = st.selectbox("Sort by", ["Priority", "Time", "Category", "Created"])
            
            # Apply filters
            filtered_tasks = st.session_state.tasks
            if priority_filter:
                filtered_tasks = [t for t in filtered_tasks if t['priority'] in priority_filter]
            if category_filter:
                filtered_tasks = [t for t in filtered_tasks if t['category'] in category_filter]
            
            # Apply sorting
            if sort_by == "Priority":
                priority_order = {"Urgent": 4, "High": 3, "Medium": 2, "Low": 1}
                filtered_tasks = sorted(filtered_tasks, key=lambda x: priority_order[x['priority']], reverse=True)
            elif sort_by == "Time":
                filtered_tasks = sorted(filtered_tasks, key=lambda x: x['estimated_time'])
            elif sort_by == "Category":
                filtered_tasks = sorted(filtered_tasks, key=lambda x: x['category'])
            
            # Display tasks
            for i, task in enumerate(filtered_tasks):
                display_task_card(task, i)
        else:
            st.info("No tasks yet. Add some tasks or get AI suggestions!")
        
        # Completed Tasks Section
        if st.session_state.completed_tasks:
            with st.expander(f"✅ Completed Tasks ({len(st.session_state.completed_tasks)})"):
                for task in st.session_state.completed_tasks:
                    st.success(f"✅ {task['title']} - Completed at {task['completed_at']}")
    
    with col2:
        # Daily Overview
        st.header("📊 Daily Overview")
        
        # Statistics
        total_tasks = len(st.session_state.tasks)
        completed_tasks = len(st.session_state.completed_tasks)
        total_time = sum(task['estimated_time'] for task in st.session_state.tasks)
        completed_time = sum(task['estimated_time'] for task in st.session_state.completed_tasks)
        
        # Stats cards
        st.markdown(f"""
        <div class="stats-container" style="color: #000;">
            <h3>📈 Progress</h3>
            <p><strong>Tasks:</strong> {completed_tasks}/{total_tasks + completed_tasks}</p>
            <p><strong>Time:</strong> {completed_time}/{total_time + completed_time} min</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Completion rate
        if total_tasks + completed_tasks > 0:
            completion_rate = completed_tasks / (total_tasks + completed_tasks) * 100
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Task breakdown by category
        if st.session_state.tasks:
            st.subheader("📂 Tasks by Category")
            category_counts = {}
            for task in st.session_state.tasks:
                category_counts[task['category']] = category_counts.get(task['category'], 0) + 1
            
            category_df = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Count'])
            st.bar_chart(category_df.set_index('Category'))
        
        # Priority breakdown
        if st.session_state.tasks:
            st.subheader("🎯 Tasks by Priority")
            priority_counts = {}
            for task in st.session_state.tasks:
                priority_counts[task['priority']] = priority_counts.get(task['priority'], 0) + 1
            
            for priority, count in priority_counts.items():
                color = PRIORITY_COLORS[priority]
                st.markdown(f"**{priority}:** {count} tasks")
        
        # Motivational Message
        if st.session_state.user_profile.get('name') and st.session_state.daily_context:
            name = st.session_state.user_profile['name']
            mood = st.session_state.daily_context.get('mood', 'Neutral')
            
            if mood in ['Good', 'Excellent']:
                motivation = f"🌟 Hey {name}! You're radiating positive energy today! Perfect time to tackle those important tasks."
            elif mood in ['Very Low', 'Low']:
                motivation = f"💙 Hi {name}, I see you're having a tough day. That's completely okay. Let's focus on small, gentle wins."
            else:
                motivation = f"✨ Hello {name}! Ready to make today count? You've got this!"
            
            st.markdown(f"""
            <div class="motivation-box">
                <h3>💬 Your Daily Motivation</h3>
                <p>{motivation}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip:** Start with small tasks to build momentum, then tackle the bigger challenges!")

if __name__ == "__main__":
    main()