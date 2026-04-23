def main():
    st.markdown("# \u2692\ufe0f Agent Forge")
    st.markdown("**Specialized AI agents with MCP tool routing.** "
                "Each agent connects to different MCP servers based on its expertise.")

    # Sidebar
    with st.sidebar:
        st.header("\U0001f511 Configuration")
        api_key = st.text_input("Anthropic API Key", type="password",
                                help="Get yours at console.anthropic.com")
        if api_key:
            os.environ["ANTHROPIC_API_KEY"] = api_key

        st.markdown("---")
        st.header("\U0001f916 Agents")
        for agent_id, agent in AGENTS.items():
            with st.expander(f"{agent.icon} {agent.name}"):
                st.markdown(f"**{agent.description}**")
                st.markdown(f"*System:* {agent.system_prompt[:100]}...")
                if agent.mcp_servers:
                    st.markdown("**MCP Servers:**")
                    for srv in agent.mcp_servers:
                        st.markdown(f"- `{srv['name']}`")

        st.markdown("---")
        st.markdown("Built with [cadre-ai](https://github.com/WeberG619/cadre-ai)")

    # Agent selection
    col1, col2 = st.columns([3, 1])
    with col2:
        mode = st.radio("Agent Selection", ["Auto-Route", "Manual"])
        if mode == "Manual":
            selected = st.selectbox(
                "Choose Agent",
                options=list(AGENTS.keys()),
                format_func=lambda x: f"{AGENTS[x].icon} {AGENTS[x].name}",
            )

    # Chat history per agent
    if "histories" not in st.session_state:
        st.session_state.histories = {k: [] for k in AGENTS}
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=msg.get("avatar")):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything..."):
        if not api_key:
            st.error("Please enter your Anthropic API key in the sidebar.")
            return

        # Route to agent
        if mode == "Auto-Route":
            agent_id = classify_query(prompt)
        else:
            agent_id = selected

        agent = AGENTS[agent_id]

        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Show routing info
        with st.chat_message("assistant", avatar=agent.icon):
            st.caption(f"Routed to **{agent.icon} {agent.name}**")
            tools_info = ", ".join(s["name"] for s in agent.mcp_servers)
            st.caption(f"MCP servers: {tools_info}" if tools_info else "No MCP servers")

            client = Anthropic(api_key=api_key)
            with st.spinner(f"{agent.name} is connecting to MCP servers..."):
                response = run_agent(
                    client, agent, prompt,
                    st.session_state.histories[agent_id],
                )

            st.markdown(response)

        # Update history
        st.session_state.histories[agent_id].append(
            {"role": "user", "content": prompt}
        )
        st.session_state.histories[agent_id].append(
            {"role": "assistant", "content": response}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "avatar": agent.icon}
        )