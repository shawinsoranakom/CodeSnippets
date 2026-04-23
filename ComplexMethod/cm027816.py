def main():
    st.set_page_config(page_title="AI Meal Planning Agent", page_icon="🍽️", layout="wide")

    st.title("🍽️ AI Meal Planning Agent")
    st.markdown("*Your intelligent companion for recipes, nutrition, and meal planning*")

    if not OPENAI_API_KEY:
        st.error("Please add OPENAI_API_KEY to your .env file")
        st.stop()

    # Initialize agent
    if "agent" not in st.session_state:
        with st.spinner("Initializing agent..."):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                st.session_state.agent = loop.run_until_complete(create_agent())
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")
                st.stop()

    # Initialize messages
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": """👋 **Welcome! I'm your AI Meal Planning Expert.**

I can help you with:
- 🔍 **Recipe Discovery** - Find recipes based on your ingredients
- 📊 **Nutrition Analysis** - Get detailed nutritional insights
- 💰 **Cost Estimation** - Smart budget planning with money-saving tips
- 📅 **Meal Planning** - Complete weekly meal plans with shopping lists

**Try asking:**
- "Find healthy chicken recipes for dinner"
- "What's the nutrition info for chicken teriyaki?"
- "Create a vegetarian meal plan for 2 people for one week"
- "Estimate costs for pasta, tomatoes, cheese, and basil for 4 servings"

What would you like to explore? 🍽️"""
        }]

    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if user_input := st.chat_input("Ask about recipes, nutrition, meal planning, or costs..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response: RunOutput = loop.run_until_complete(
                        st.session_state.agent.arun(user_input)
                    )

                    st.markdown(response.content)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.content
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })