def render_multi_sessions(support_agent, sales_agent):
    """Render the multi-sessions demo"""
    st.header("👥 Multi Sessions Demo")
    st.markdown("Demonstrates managing multiple conversations and different agent contexts.")

    tab1, tab2, tab3 = st.tabs(["👤 Multi-User", "🏢 Context-Based", "🔄 Agent Handoff"])

    with tab1:
        st.subheader("Different Users, Separate Sessions")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**👩 Alice's Session**")
            alice_session_id = "user_alice"

            with st.form("alice_form"):
                alice_input = st.text_input("Alice's message:", key="alice_input")
                alice_submitted = st.form_submit_button("Send as Alice")

                if alice_submitted and alice_input:
                    with st.spinner("Processing Alice's message..."):
                        session = st.session_state.session_manager.get_session(alice_session_id, "multi_user.db")
                        result = asyncio.run(Runner.run(support_agent, alice_input, session=session))
                        st.write(f"**Support:** {result.final_output}")

            if st.button("📋 Alice's History", key="alice_history"):
                items = asyncio.run(st.session_state.session_manager.get_session_items(alice_session_id))
                for item in items:
                    role_emoji = "👩" if item['role'] == 'user' else "🛠️"
                    st.write(f"{role_emoji} **{item['role'].title()}:** {item['content']}")

        with col2:
            st.write("**👨 Bob's Session**")
            bob_session_id = "user_bob"

            with st.form("bob_form"):
                bob_input = st.text_input("Bob's message:", key="bob_input")
                bob_submitted = st.form_submit_button("Send as Bob")

                if bob_submitted and bob_input:
                    with st.spinner("Processing Bob's message..."):
                        session = st.session_state.session_manager.get_session(bob_session_id, "multi_user.db")
                        result = asyncio.run(Runner.run(support_agent, bob_input, session=session))
                        st.write(f"**Support:** {result.final_output}")

            if st.button("📋 Bob's History", key="bob_history"):
                items = asyncio.run(st.session_state.session_manager.get_session_items(bob_session_id))
                for item in items:
                    role_emoji = "👨" if item['role'] == 'user' else "🛠️"
                    st.write(f"{role_emoji} **{item['role'].title()}:** {item['content']}")

    with tab2:
        st.subheader("Different Contexts, Different Sessions")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**🛠️ Support Context**")
            support_session_id = "support_context"

            with st.form("support_context_form"):
                support_input = st.text_input("Support question:", key="support_context_input")
                support_submitted = st.form_submit_button("Ask Support")

                if support_submitted and support_input:
                    with st.spinner("Processing support question..."):
                        session = st.session_state.session_manager.get_session(support_session_id, "contexts.db")
                        result = asyncio.run(Runner.run(support_agent, support_input, session=session))
                        st.write(f"**Support:** {result.final_output}")

        with col2:
            st.write("**💰 Sales Context**")
            sales_session_id = "sales_context"

            with st.form("sales_context_form"):
                sales_input = st.text_input("Sales inquiry:", key="sales_context_input")
                sales_submitted = st.form_submit_button("Ask Sales")

                if sales_submitted and sales_input:
                    with st.spinner("Processing sales inquiry..."):
                        session = st.session_state.session_manager.get_session(sales_session_id, "contexts.db")
                        result = asyncio.run(Runner.run(sales_agent, sales_input, session=session))
                        st.write(f"**Sales:** {result.final_output}")

    with tab3:
        st.subheader("Shared Session Across Different Agents")
        st.caption("Customer handoff scenario - same conversation, different agents")

        shared_session_id = "customer_handoff"

        # Agent selector
        selected_agent = st.radio(
            "Select Agent:",
            ["Sales Agent", "Support Agent"],
            horizontal=True
        )

        agent = sales_agent if selected_agent == "Sales Agent" else support_agent

        with st.form("handoff_form"):
            handoff_input = st.text_input("Customer message:")
            handoff_submitted = st.form_submit_button(f"Send to {selected_agent}")

            if handoff_submitted and handoff_input:
                with st.spinner(f"Processing with {selected_agent}..."):
                    session = st.session_state.session_manager.get_session(shared_session_id, "shared.db")
                    result = asyncio.run(Runner.run(agent, handoff_input, session=session))
                    st.write(f"**{selected_agent}:** {result.final_output}")

        # Show shared conversation history
        if st.button("📋 Show Shared Conversation"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(shared_session_id))
            if items:
                st.write("**Shared Conversation History:**")
                for i, item in enumerate(items, 1):
                    if item['role'] == 'user':
                        st.write(f"{i}. 👤 **Customer:** {item['content']}")
                    else:
                        # Try to determine which agent responded based on content
                        agent_emoji = "💰" if "sales" in item['content'].lower() or "price" in item['content'].lower() else "🛠️"
                        st.write(f"{i}. {agent_emoji} **Agent:** {item['content']}")
            else:
                st.info("No conversation history yet.")