def render_basic_sessions(agent):
    """Render the basic sessions demo"""
    st.header("📝 Basic Sessions Demo")
    st.markdown("Demonstrates fundamental session memory with automatic conversation history.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💾 In-Memory Session")
        st.caption("Temporary session storage (lost when app restarts)")

        session_id = "in_memory_demo"

        with st.form("in_memory_form"):
            user_input = st.text_input("Your message:", key="in_memory_input")
            submitted = st.form_submit_button("Send Message")

            if submitted and user_input:
                with st.spinner("Processing..."):
                    session = st.session_state.session_manager.get_session(session_id)
                    result = asyncio.run(Runner.run(agent, user_input, session=session))

                    st.success("Message sent!")
                    st.write(f"**Assistant:** {result.final_output}")

        # Show conversation history
        if st.button("📋 Show Conversation", key="show_in_memory"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write("**Conversation History:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")

    with col2:
        st.subheader("💽 Persistent Session")
        st.caption("File-based storage (survives app restarts)")

        session_id = "persistent_demo"

        with st.form("persistent_form"):
            user_input = st.text_input("Your message:", key="persistent_input")
            submitted = st.form_submit_button("Send Message")

            if submitted and user_input:
                with st.spinner("Processing..."):
                    session = st.session_state.session_manager.get_session(session_id, "persistent_demo.db")
                    result = asyncio.run(Runner.run(agent, user_input, session=session))

                    st.success("Message sent!")
                    st.write(f"**Assistant:** {result.final_output}")

        # Show conversation history
        if st.button("📋 Show Conversation", key="show_persistent"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write("**Conversation History:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")