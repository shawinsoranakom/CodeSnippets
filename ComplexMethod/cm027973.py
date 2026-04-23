def render_memory_operations(agent):
    """Render the memory operations demo"""
    st.header("🧠 Memory Operations Demo")
    st.markdown("Demonstrates advanced session memory operations including item manipulation and corrections.")

    session_id = "memory_operations_demo"

    # Main conversation area
    st.subheader("💬 Conversation")
    with st.form("memory_conversation"):
        user_input = st.text_input("Your message:")
        submitted = st.form_submit_button("Send Message")

        if submitted and user_input:
            with st.spinner("Processing..."):
                session = st.session_state.session_manager.get_session(session_id)
                result = asyncio.run(Runner.run(agent, user_input, session=session))

                st.success("Message sent!")
                st.write(f"**Assistant:** {result.final_output}")

    # Memory operations
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Memory Inspection")

        if st.button("🔍 Get All Items"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write(f"**Total items:** {len(items)}")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    content_preview = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {content_preview}")
            else:
                st.info("No items in session yet.")

        # Get limited items
        limit = st.number_input("Get last N items:", min_value=1, max_value=20, value=3)
        if st.button("📋 Get Recent Items"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id, limit=limit))
            if items:
                st.write(f"**Last {len(items)} items:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No items to show.")

    with col2:
        st.subheader("✏️ Memory Manipulation")

        # Add custom items
        st.write("**Add Custom Items:**")
        with st.form("add_items_form"):
            user_content = st.text_area("User message to add:")
            assistant_content = st.text_area("Assistant response to add:")
            add_submitted = st.form_submit_button("➕ Add Items")

            if add_submitted and user_content and assistant_content:
                custom_items = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content}
                ]
                asyncio.run(st.session_state.session_manager.add_custom_items(session_id, custom_items))
                st.success("Custom items added!")

        # Pop last item (correction)
        if st.button("↶ Undo Last Response"):
            popped_item = asyncio.run(st.session_state.session_manager.pop_last_item(session_id))
            if popped_item:
                st.success(f"Removed: {popped_item['role']} - {popped_item['content'][:50]}...")
            else:
                st.warning("No items to remove.")

        # Clear session
        if st.button("🗑️ Clear Session"):
            asyncio.run(st.session_state.session_manager.clear_session(session_id))
            st.success("Session cleared!")