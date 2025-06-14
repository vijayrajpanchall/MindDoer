# AI Life Coach Agent

An intelligent personal life coaching system built with LangChain and Python that helps users manage tasks, stay motivated, and achieve their goals.

## 🌟 Features

- **Smart Task Management**
  - User-created and AI-suggested tasks
  - Priority-based task organization
  - Energy level-aware scheduling
  - Progress tracking

- **Context-Aware Assistance**
  - Mood tracking
  - Energy level monitoring
  - Stress level assessment
  - Available time management

- **Personalized Coaching**
  - Motivational messages
  - Daily insights
  - Goal-oriented suggestions
  - Stress management recommendations

## 🚀 Getting Started

### Prerequisites

Install the required dependencies:

```sh
pip install -r requirements.txt
```

### Environment Setup

1. Create a `.env` file in the project root
2. Add your API keys and configurations
3. Ensure FAISS index directory exists

### Running the Application

```sh
python agent.py
```

## 💡 Usage

1. **Initial Setup**
   - Enter your name
   - Set your current mood and energy levels
   - Input your goals
   - Add custom tasks

2. **Daily Interaction**
   - View personalized task list
   - Add new tasks
   - Mark tasks as complete
   - Get motivational support

3. **Task Management Options**
   - Add new tasks during the day
   - Mark tasks as complete
   - View current task list
   - Exit the application

## 🏗️ Project Structure

- `agent.py`: Main application logic and agent implementation
- `goal_memory.py`: Goal storage and retrieval system
- `goal_memory_index/`: FAISS vector store for goals

## 🛠️ Technical Components

- **State Management**: TypedDict based state system
- **Workflow Engine**: LangGraph for agent workflow
- **Vector Store**: FAISS for goal memory
- **Task System**: Priority and energy-based task management
- **Interactive Interface**: Command-line interface for user interaction

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request