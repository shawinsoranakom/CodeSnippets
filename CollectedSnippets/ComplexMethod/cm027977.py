def render_conversation_management(agent, model_choice, temperature, max_turns):
    """Render the conversation management demo"""
    st.header("💬 Conversation Management Demo")
    st.markdown("Compare manual conversation threading vs automatic session management.")

    tab1, tab2 = st.tabs(["Manual Threading", "Session Management"])

    with tab1:
        st.subheader("🔧 Manual Conversation Threading")
        st.caption("Using result.to_input_list() for conversation history")

        # Initialize conversation history in session state
        if 'manual_conversation' not in st.session_state:
            st.session_state.manual_conversation = []

        with st.form("manual_form"):
            manual_input = st.text_input("Your message:")
            manual_submitted = st.form_submit_button("Send Message")

            if manual_submitted and manual_input:
                with st.spinner("Processing..."):
                    try:
                        # Build input list manually
                        input_list = st.session_state.manual_conversation.copy()
                        input_list.append({"role": "user", "content": manual_input})

                        result = asyncio.run(Runner.run(agent, input_list))

                        # Update conversation history
                        st.session_state.manual_conversation = result.to_input_list()

                        st.success("Message sent!")
                        st.write(f"**Assistant:** {result.final_output}")

                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        # Show conversation history
        if st.button("📋 Show Manual History"):
            if st.session_state.manual_conversation:
                st.write("**Conversation History:**")
                for i, item in enumerate(st.session_state.manual_conversation, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")

        if st.button("🗑️ Clear Manual History"):
            st.session_state.manual_conversation = []
            st.success("Manual conversation history cleared!")

    with tab2:
        st.subheader("🔄 Automatic Session Management")
        st.caption("Using SQLiteSession for automatic conversation memory")

        session_id = "demo_conversation"

        with st.form("session_form"):
            session_input = st.text_input("Your message:")
            session_submitted = st.form_submit_button("Send Message")

            if session_submitted and session_input:
                with st.spinner("Processing..."):
                    try:
                        # Get or create session
                        if session_id not in st.session_state.session_manager:
                            st.session_state.session_manager[session_id] = SQLiteSession(session_id)

                        session = st.session_state.session_manager[session_id]
                        result = asyncio.run(Runner.run(agent, session_input, session=session))

                        st.success("Message sent!")
                        st.write(f"**Assistant:** {result.final_output}")

                    except Exception as e:
                        st.error(f"❌ Error: {e}")

        # Show session history
        if st.button("📋 Show Session History"):
            if session_id in st.session_state.session_manager:
                session = st.session_state.session_manager[session_id]
                try:
                    items = asyncio.run(session.get_items())
                    if items:
                        st.write("**Session History:**")
                        for i, item in enumerate(items, 1):
                            role_emoji = "👤" if item['role'] == 'user' else "🤖"
                            st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
                    else:
                        st.info("No session history yet.")
                except Exception as e:
                    st.error(f"❌ Error retrieving history: {e}")
            else:
                st.info("No session created yet.")

        if st.button("🗑️ Clear Session History"):
            if session_id in st.session_state.session_manager:
                try:
                    session = st.session_state.session_manager[session_id]
                    asyncio.run(session.clear_session())
                    del st.session_state.session_manager[session_id]
                    st.success("Session history cleared!")
                except Exception as e:
                    st.error(f"❌ Error clearing session: {e}")