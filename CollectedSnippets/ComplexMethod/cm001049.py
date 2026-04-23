async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        agent_json: dict[str, Any] | None = None,
        save: bool = True,
        library_agent_ids: list[str] | None = None,
        folder_id: str | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        session_id = session.session_id if session else None

        guide_gate = require_guide_read(session, "create_agent")
        if guide_gate is not None:
            return guide_gate

        if not agent_json:
            return ErrorResponse(
                message=(
                    "Please provide agent_json with the complete agent graph. "
                    "Use find_block to discover blocks, then generate the JSON."
                ),
                error="missing_agent_json",
                session_id=session_id,
            )

        if library_agent_ids is None:
            library_agent_ids = []

        nodes = agent_json.get("nodes", [])
        if not nodes:
            return ErrorResponse(
                message="The agent JSON has no nodes. An agent needs at least one block.",
                error="empty_agent",
                session_id=session_id,
            )

        # Ensure top-level fields
        if "id" not in agent_json:
            agent_json["id"] = str(uuid.uuid4())
        if "version" not in agent_json:
            agent_json["version"] = 1
        if "is_active" not in agent_json:
            agent_json["is_active"] = True

        # Fetch library agents for AgentExecutorBlock validation
        library_agents = await fetch_library_agents(user_id, library_agent_ids)

        return await fix_validate_and_save(
            agent_json,
            user_id=user_id,
            session_id=session_id,
            save=save,
            is_update=False,
            default_name="Generated Agent",
            library_agents=library_agents,
            folder_id=folder_id,
        )