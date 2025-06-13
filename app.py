# Streamlit UI and app entry point

import streamlit as st

def main():
    st.title("MindDoer - Daily Mood & Energy Check-in")

    st.write("Please input your current mood and energy level to get your personalized tasks.")

    # Mood input (1 to 5)
    mood = st.slider("How is your mood today?", min_value=1, max_value=5, value=3, help="1 = very low, 5 = very high")
    print(f"mood{mood}")
    # Energy input (1 to 5)
    energy = st.slider("How is your energy level today?", min_value=1, max_value=5, value=3, help="1 = very low, 5 = very high")

    if st.button("Submit"):
        st.success(f"Got it! Your mood is {mood} and your energy level is {energy}.")
        # Here you will later call your LangChain agent to generate tasks based on these inputs

if __name__ == "__main__":
    main()
