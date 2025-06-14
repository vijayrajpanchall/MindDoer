from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import END, StateGraph
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

# Initialize components
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(temperature=0.7)

# Load existing vector store (your goal memory)
try:
    vectorstore = FAISS.load_local("goal_memory_index", embeddings, allow_dangerous_deserialization=True)
    print("✅ Loaded existing goal memory")
except FileNotFoundError:
    vectorstore = FAISS.from_texts(["Personal goals and habits"], embeddings)
    print("🆕 Created new goal memory")

# Enums for better type safety
class MoodLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    NEUTRAL = 3
    GOOD = 4
    EXCELLENT = 5

class EnergyLevel(Enum):
    EXHAUSTED = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    PEAK = 5

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"
    RESCHEDULED = "rescheduled"

# Data structures
class Task(TypedDict):
    id: str
    title: str
    description: str
    priority: TaskPriority
    estimated_time: int  # minutes
    category: str  # work, personal, health, learning
    deadline: Optional[str]
    energy_required: EnergyLevel
    status: TaskStatus
    created_at: str
    completed_at: Optional[str]
    user_created: bool  # NEW: Track if user created this task

class UserProfile(TypedDict):
    name: str
    timezone: str
    sleep_schedule: Dict[str, str]  # bedtime, wake_time
    work_schedule: Dict[str, List[str]]  # days and hours
    gym_schedule: List[str]  # preferred days
    personality_traits: List[str]
    motivation_style: str  # encouraging, direct, analytical
    procrastination_patterns: Dict[str, str]

class DailyContext(TypedDict):
    date: str
    mood: MoodLevel
    energy: EnergyLevel
    available_time_blocks: List[Dict[str, str]]
    calendar_events: List[Dict[str, str]]
    weather: Optional[str]
    stress_level: int  # 1-10

# Main Agent State
class LifeCoachState(TypedDict):
    user_profile: UserProfile
    daily_context: DailyContext
    current_tasks: List[Task]
    completed_tasks: List[Task]
    missed_tasks: List[Task]
    goals: List[str]
    habits_tracking: Dict[str, List[bool]]  # habit_name: [day1, day2, ...]
    motivation_message: str
    daily_todo_list: List[Task]
    reflection_insights: str
    next_action: str
    agent_status: str
    user_input_mode: bool  # NEW: Flag for user input mode
    pending_user_tasks: List[Dict]  # NEW: Store user's custom tasks

# =============================================================================
# USER INTERACTION FUNCTIONS
# =============================================================================

class LifeCoachInterface:
    def __init__(self):
        self.state = None
        self.app = None
    
    def get_user_input(self):
        """Collect user's daily context and goals"""
        print("\n🌟 Welcome to your Personal AI Life Coach!")
        print("Let's start by understanding your day...")
        
        # Get basic info
        name = input("What's your name? ") or "User"
        
        # Get mood
        print("\nHow are you feeling today?")
        print("1. Very Low  2. Low  3. Neutral  4. Good  5. Excellent")
        mood_input = input("Enter number (1-5): ") or "3"
        mood = MoodLevel(int(mood_input))
        
        # Get energy
        print("\nWhat's your energy level?")
        print("1. Exhausted  2. Low  3. Moderate  4. High  5. Peak")
        energy_input = input("Enter number (1-5): ") or "3"
        energy = EnergyLevel(int(energy_input))
        
        # Get stress level
        stress_input = input("Stress level (1-10): ") or "5"
        stress_level = int(stress_input)
        
        # Get available time
        print("\nHow many hours do you have available today for tasks?")
        available_hours = input("Hours (e.g., 4): ") or "4"
        
        # Create time blocks based on available hours
        available_time_blocks = []
        hours = int(float(available_hours))
        current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        for i in range(0, hours, 2):  # 2-hour blocks
            block_duration = min(2, hours - i)
            start_time = current_time + timedelta(hours=i)
            end_time = start_time + timedelta(hours=block_duration)
            available_time_blocks.append({
                "start": start_time.strftime("%I:%M %p"),
                "end": end_time.strftime("%I:%M %p")
            })
        
        return {
            "name": name,
            "mood": mood,
            "energy": energy,
            "stress_level": stress_level,
            "available_time_blocks": available_time_blocks
        }
    
    def get_user_goals(self):
        """Get user's goals and priorities"""
        print("\n🎯 Let's talk about your goals...")
        goals = []
        
        print("Enter your goals (press Enter after each, empty line to finish):")
        while True:
            goal = input("Goal: ").strip()
            if not goal:
                break
            goals.append(goal)
            
        return goals
    
    def get_custom_tasks(self):
        """Allow user to add their own tasks"""
        print("\n📝 Want to add your own tasks? (y/n)")
        if input().lower().startswith('y'):
            custom_tasks = []
            
            print("Add your custom tasks (press Enter after each, empty title to finish):")
            while True:
                title = input("Task title: ").strip()
                if not title:
                    break
                
                description = input("Description (optional): ").strip() or title
                
                print("Priority: 1-Low, 2-Medium, 3-High, 4-Urgent")
                priority_input = input("Priority (1-4): ") or "2"
                priority = TaskPriority(int(priority_input))
                
                time_input = input("Estimated time (minutes): ") or "30"
                estimated_time = int(time_input)
                
                category = input("Category (work/personal/health/learning): ") or "personal"
                
                print("Energy required: 1-Low, 2-Moderate, 3-High")
                energy_input = input("Energy (1-3): ") or "2"
                energy_map = {1: EnergyLevel.LOW, 2: EnergyLevel.MODERATE, 3: EnergyLevel.HIGH}
                energy_required = energy_map[int(energy_input)]
                
                custom_task = {
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "estimated_time": estimated_time,
                    "category": category,
                    "energy_required": energy_required
                }
                custom_tasks.append(custom_task)
                print(f"✅ Added: {title}")
            
            return custom_tasks
        return []
    
    def display_tasks(self, tasks: List[Task]):
        """Display tasks in a user-friendly format"""
        if not tasks:
            print("No tasks for today.")
            return
            
        print("\n📋 YOUR TASKS FOR TODAY:")
        print("=" * 50)
        
        for i, task in enumerate(tasks, 1):
            user_indicator = "👤" if task.get('user_created', False) else "🤖"
            print(f"{i}. {user_indicator} {task['title']}")
            print(f"   📝 {task['description']}")
            print(f"   ⏱️  {task['estimated_time']} min | ⚡ {task['energy_required'].name} energy")
            print(f"   📊 {task['priority'].name} priority | 📂 {task['category']}")
            print()
    
    def interactive_session(self):
        """Run an interactive session with the user"""
        # Get user input
        user_data = self.get_user_input()
        goals = self.get_user_goals()
        custom_tasks = self.get_custom_tasks()
        
        # Create user profile
        user_profile = UserProfile(
            name=user_data["name"],
            timezone="Local",
            sleep_schedule={"bedtime": "11:00 PM", "wake_time": "7:00 AM"},
            work_schedule={"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "hours": ["9 AM", "5 PM"]},
            gym_schedule=["Monday", "Wednesday", "Friday"],
            personality_traits=["motivated", "goal-oriented"],
            motivation_style="encouraging",
            procrastination_patterns={}
        )
        
        # Create daily context
        daily_context = DailyContext(
            date=datetime.now().strftime("%Y-%m-%d"),
            mood=user_data["mood"],
            energy=user_data["energy"],
            available_time_blocks=user_data["available_time_blocks"],
            calendar_events=[],
            weather="Unknown",
            stress_level=user_data["stress_level"]
        )
        
        # Create initial state
        initial_state = LifeCoachState(
            user_profile=user_profile,
            daily_context=daily_context,
            current_tasks=[],
            completed_tasks=[],
            missed_tasks=[],
            goals=goals,
            habits_tracking={},
            motivation_message="",
            daily_todo_list=[],
            reflection_insights="",
            next_action="",
            agent_status="initialized",
            user_input_mode=True,
            pending_user_tasks=custom_tasks
        )
        
        return initial_state

# =============================================================================
# ENHANCED NODES WITH USER TASK INTEGRATION
# =============================================================================

def user_task_integrator_node(state: LifeCoachState) -> LifeCoachState:
    """Integrates user's custom tasks with AI-generated tasks"""
    
    user_tasks = []
    
    # Convert user's custom tasks to Task objects
    for custom_task in state.get("pending_user_tasks", []):
        task = Task(
            id=str(uuid.uuid4()),
            title=custom_task["title"],
            description=custom_task["description"],
            priority=custom_task["priority"],
            estimated_time=custom_task["estimated_time"],
            category=custom_task["category"],
            deadline=None,
            energy_required=custom_task["energy_required"],
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            user_created=True  # Mark as user-created
        )
        user_tasks.append(task)
    
    return {
        **state,
        "current_tasks": user_tasks,
        "agent_status": "User tasks integrated"
    }

def enhanced_task_generator_node(state: LifeCoachState) -> LifeCoachState:
    """Enhanced task generator that respects user tasks"""
    
    daily_context = state["daily_context"]
    goals = state["goals"]
    user_tasks = state["current_tasks"]  # User's custom tasks
    
    # Start with user tasks
    all_tasks = user_tasks.copy()
    task_counter = len(user_tasks) + 1
    
    # Add AI-suggested tasks only if there's room
    total_user_time = sum(task["estimated_time"] for task in user_tasks)
    available_time = sum(2 * 60 for _ in daily_context["available_time_blocks"])  # 2 hours per block in minutes
    remaining_time = available_time - total_user_time
    
    if remaining_time > 30:  # At least 30 minutes left
        # Add goal-based tasks if user has goals
        for goal in goals[:1]:  # Only 1 additional goal task
            if remaining_time > 45:
                goal_task = Task(
                    id=f"ai_task_{task_counter}",
                    title=f"Progress: {goal[:25]}...",
                    description=f"Take a step towards: {goal}",
                    priority=TaskPriority.MEDIUM,
                    estimated_time=30,
                    category="personal",
                    deadline=None,
                    energy_required=EnergyLevel.MODERATE,
                    status=TaskStatus.PENDING,
                    created_at=datetime.now().isoformat(),
                    completed_at=None,
                    user_created=False
                )
                all_tasks.append(goal_task)
                remaining_time -= 30
                task_counter += 1
    
    # Add wellness task if stressed
    if daily_context["stress_level"] >= 6 and remaining_time > 15:
        wellness_task = Task(
            id=f"ai_task_{task_counter}",
            title="Stress Relief Break",
            description="Take time for yourself - breathe, walk, or relax",
            priority=TaskPriority.HIGH,
            estimated_time=15,
            category="health",
            deadline=None,
            energy_required=EnergyLevel.LOW,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            user_created=False
        )
        all_tasks.append(wellness_task)
    
    return {
        **state,
        "daily_todo_list": all_tasks,
        "current_tasks": all_tasks,
        "agent_status": "Enhanced tasks generated with user input"
    }

def context_analyzer_node(state: LifeCoachState) -> LifeCoachState:
    """Analyzes current context and mood to understand the user's situation"""
    
    daily_context = state["daily_context"]
    user_profile = state["user_profile"]
    
    context_analysis = f"""
    📊 Today's Context Analysis for {user_profile['name']}:
    - Mood: {daily_context['mood'].name} 
    - Energy: {daily_context['energy'].name}
    - Available time: {len(daily_context['available_time_blocks'])} blocks
    - Stress level: {daily_context['stress_level']}/10
    """
    
    if daily_context['energy'].value >= 4:
        context_analysis += "\n✨ High energy day - great for challenging tasks!"
    elif daily_context['energy'].value <= 2:
        context_analysis += "\n🌱 Low energy day - focus on gentle, nurturing activities"
    
    if daily_context['stress_level'] >= 7:
        context_analysis += "\n🧘 High stress detected - prioritizing self-care"
    
    return {
        **state,
        "reflection_insights": context_analysis,
        "agent_status": "Context analyzed"
    }

def motivation_coach_node(state: LifeCoachState) -> LifeCoachState:
    """Generates personalized motivational messages"""
    
    user_profile = state["user_profile"]
    daily_context = state["daily_context"]
    user_tasks = [t for t in state["current_tasks"] if t.get("user_created", False)]
    
    name = user_profile["name"]
    
    if daily_context["mood"].value >= 4:
        base_message = f"🌟 Hey {name}! You're radiating positive energy today! "
    elif daily_context["mood"].value <= 2:
        base_message = f"💙 Hi {name}, I see you're having a tough day. That's completely okay. "
    else:
        base_message = f"✨ Hello {name}! Ready to make today count? "
    
    if user_tasks:
        coaching_message = f"""
        {base_message}
        
        I love that you've added {len(user_tasks)} of your own tasks! That shows real ownership of your goals.
        
        🎯 Your personal tasks show you know what matters to you.
        💪 I've added a few suggestions to complement your plan.
        🌱 Remember: you're in control of your day!
        
        Let's make it happen together! 
        """
    else:
        coaching_message = f"""
        {base_message}
        
        I've created a personalized plan based on your goals and energy level.
        
        🎯 Each task is designed to match your current state
        💪 You've got the energy to tackle these challenges
        🌱 Small steps today lead to big wins tomorrow
        
        You've got this, {name}!
        """
    
    return {
        **state,
        "motivation_message": coaching_message,
        "agent_status": "Motivation message ready"
    }

# =============================================================================
# ENHANCED GRAPH CONSTRUCTION
# =============================================================================

def create_enhanced_life_coach_graph():
    """Creates the enhanced Life Coach Agent workflow with user integration"""
    
    graph = StateGraph(LifeCoachState)
    
    # Add nodes
    graph.add_node("context_analyzer", context_analyzer_node)
    graph.add_node("user_task_integrator", user_task_integrator_node)
    graph.add_node("enhanced_task_generator", enhanced_task_generator_node)
    graph.add_node("motivation_coach", motivation_coach_node)
    
    # Set entry point
    graph.set_entry_point("context_analyzer")
    
    # Define workflow
    graph.add_edge("context_analyzer", "user_task_integrator")
    graph.add_edge("user_task_integrator", "enhanced_task_generator")
    graph.add_edge("enhanced_task_generator", "motivation_coach")
    graph.add_edge("motivation_coach", END)
    
    return graph.compile()

# =============================================================================
# TASK MANAGEMENT FUNCTIONS
# =============================================================================

def mark_task_complete(state: LifeCoachState, task_id: str) -> LifeCoachState:
    """Mark a specific task as completed"""
    updated_tasks = []
    completed_task = None
    
    for task in state["current_tasks"]:
        if task["id"] == task_id:
            task["status"] = TaskStatus.COMPLETED
            task["completed_at"] = datetime.now().isoformat()
            completed_task = task
        updated_tasks.append(task)
    
    completed_tasks = state.get("completed_tasks", [])
    if completed_task:
        completed_tasks.append(completed_task)
    
    return {
        **state,
        "current_tasks": updated_tasks,
        "completed_tasks": completed_tasks
    }

def add_new_task(state: LifeCoachState, title: str, description: str = "", priority: TaskPriority = TaskPriority.MEDIUM, estimated_time: int = 30, category: str = "personal") -> LifeCoachState:
    """Add a new task during the day"""
    new_task = Task(
        id=str(uuid.uuid4()),
        title=title,
        description=description or title,
        priority=priority,
        estimated_time=estimated_time,
        category=category,
        deadline=None,
        energy_required=EnergyLevel.MODERATE,
        status=TaskStatus.PENDING,
        created_at=datetime.now().isoformat(),
        completed_at=None,
        user_created=True
    )
    
    current_tasks = state["current_tasks"] + [new_task]
    daily_todo_list = state["daily_todo_list"] + [new_task]
    
    return {
        **state,
        "current_tasks": current_tasks,
        "daily_todo_list": daily_todo_list
    }

# =============================================================================
# MAIN INTERACTIVE APPLICATION
# =============================================================================

def main():
    """Main interactive application"""
    print("🤖 Personal AI Life Coach Agent")
    print("=" * 50)
    
    # Create interface
    interface = LifeCoachInterface()
    
    # Get user input and create initial state
    initial_state = interface.interactive_session()
    
    # Create and run the enhanced graph
    life_coach_app = create_enhanced_life_coach_graph()
    final_state = life_coach_app.invoke(initial_state)
    
    # Display results
    print("\n🎯 YOUR PERSONALIZED DAILY PLAN")
    print("=" * 50)
    
    print(f"\n💭 MOTIVATION MESSAGE:")
    print(final_state['motivation_message'])
    
    interface.display_tasks(final_state['daily_todo_list'])
    
    print(f"\n🔍 INSIGHTS:")
    print(final_state['reflection_insights'])
    
    # Interactive task management
    while True:
        print("\n" + "=" * 30)
        print("What would you like to do?")
        print("1. Add a new task")
        print("2. Mark task as complete")
        print("3. View current tasks")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            title = input("Task title: ").strip()
            if title:
                description = input("Description (optional): ").strip()
                print("Priority: 1-Low, 2-Medium, 3-High, 4-Urgent")
                priority_input = input("Priority (1-4): ") or "2"
                priority = TaskPriority(int(priority_input))
                time_input = input("Estimated time (minutes): ") or "30"
                estimated_time = int(time_input)
                category = input("Category (work/personal/health/learning): ") or "personal"
                
                final_state = add_new_task(final_state, title, description, priority, estimated_time, category)
                print(f"✅ Added task: {title}")
        
        elif choice == "2":
            interface.display_tasks(final_state['current_tasks'])
            task_num = input("Enter task number to complete: ").strip()
            try:
                task_index = int(task_num) - 1
                if 0 <= task_index < len(final_state['current_tasks']):
                    task_id = final_state['current_tasks'][task_index]['id']
                    final_state = mark_task_complete(final_state, task_id)
                    print("✅ Task marked as complete!")
                else:
                    print("Invalid task number.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "3":
            interface.display_tasks(final_state['current_tasks'])
        
        elif choice == "4":
            print("🌟 Great job today! Remember: Progress > Perfection")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()