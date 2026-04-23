async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        agent_ids: list[str] | None = None,
        folder_id: str | None = None,
        **kwargs,
    ) -> ToolResponseBase:
        """Move one or more agents to a folder or to root level."""
        assert user_id is not None  # guaranteed by requires_auth
        if agent_ids is None:
            agent_ids = []
        session_id = session.session_id if session else None

        if not agent_ids:
            return ErrorResponse(
                message="Please provide at least one agent ID.",
                error="missing_agent_ids",
                session_id=session_id,
            )

        try:
            moved = await library_db().bulk_move_agents_to_folder(
                agent_ids=agent_ids,
                folder_id=folder_id,
                user_id=user_id,
            )
        except Exception as e:
            return ErrorResponse(
                message=f"Failed to move agents: {e}",
                error="move_agents_failed",
                session_id=session_id,
            )

        moved_ids = [a.id for a in moved]
        agent_names = [a.name for a in moved]
        dest = "the folder" if folder_id else "root level"
        names_str = (
            ", ".join(agent_names) if agent_names else f"{len(agent_ids)} agent(s)"
        )
        return AgentsMovedToFolderResponse(
            message=f"Moved {names_str} to {dest}.",
            agent_ids=moved_ids,
            agent_names=agent_names,
            folder_id=folder_id,
            count=len(moved),
            session_id=session_id,
        )