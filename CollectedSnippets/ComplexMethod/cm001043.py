async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        parent_id: str | None = None,
        include_agents: bool = False,
        **kwargs,
    ) -> ToolResponseBase:
        """List folders as a flat list (by parent) or full tree."""
        assert user_id is not None  # guaranteed by requires_auth
        session_id = session.session_id if session else None

        try:
            if parent_id:
                folders = await library_db().list_folders(
                    user_id=user_id, parent_id=parent_id
                )
                raw_map = (
                    await library_db().get_folder_agents_map(
                        user_id, [f.id for f in folders]
                    )
                    if include_agents
                    else None
                )
                agents_map = _to_agent_summaries_map(raw_map) if raw_map else None
                return FolderListResponse(
                    message=f"Found {len(folders)} folder(s).",
                    folders=[
                        _folder_to_info(f, agents_map.get(f.id) if agents_map else None)
                        for f in folders
                    ],
                    count=len(folders),
                    session_id=session_id,
                )
            else:
                tree = await library_db().get_folder_tree(user_id=user_id)
                all_ids = collect_tree_ids(tree)
                agents_map = None
                root_agents = None
                if include_agents:
                    raw_map = await library_db().get_folder_agents_map(user_id, all_ids)
                    agents_map = _to_agent_summaries_map(raw_map)
                    root_agents = _to_agent_summaries(
                        await library_db().get_root_agent_summaries(user_id)
                    )
                return FolderListResponse(
                    message=f"Found {len(all_ids)} folder(s) in your library.",
                    tree=[_tree_to_info(t, agents_map) for t in tree],
                    root_agents=root_agents,
                    count=len(all_ids),
                    session_id=session_id,
                )
        except Exception as e:
            return ErrorResponse(
                message=f"Failed to list folders: {e}",
                error="list_folders_failed",
                session_id=session_id,
            )