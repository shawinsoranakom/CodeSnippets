async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        query: str = "",
        **kwargs,
    ) -> ToolResponseBase:
        if not user_id:
            return ErrorResponse(
                message="Authentication required.",
                session_id=session.session_id,
            )

        if not await is_enabled_for_user(user_id):
            return ErrorResponse(
                message="Memory features are not enabled for your account.",
                session_id=session.session_id,
            )

        if not query:
            return ErrorResponse(
                message="A search query is required to find memories to forget.",
                session_id=session.session_id,
            )

        try:
            group_id = derive_group_id(user_id)
        except ValueError:
            return ErrorResponse(
                message="Invalid user ID for memory operations.",
                session_id=session.session_id,
            )

        try:
            client = await get_graphiti_client(group_id)
            edges = await client.search(
                query=query,
                group_ids=[group_id],
                num_results=10,
            )
        except Exception:
            logger.warning(
                "Memory forget search failed for user %s", user_id[:12], exc_info=True
            )
            return ErrorResponse(
                message="Memory search is temporarily unavailable.",
                session_id=session.session_id,
            )

        if not edges:
            return MemoryForgetCandidatesResponse(
                message="No matching memories found.",
                session_id=session.session_id,
                candidates=[],
            )

        candidates = []
        for e in edges:
            edge_uuid = getattr(e, "uuid", None) or getattr(e, "id", None)
            if not edge_uuid:
                continue
            fact = extract_fact(e)
            valid_from, valid_to = extract_temporal_validity(e)
            candidates.append(
                {
                    "uuid": str(edge_uuid),
                    "fact": fact,
                    "valid_from": str(valid_from),
                    "valid_to": str(valid_to),
                }
            )

        return MemoryForgetCandidatesResponse(
            message=f"Found {len(candidates)} candidate(s). Show these to the user and ask which to delete, then call memory_forget_confirm with the UUIDs.",
            session_id=session.session_id,
            candidates=candidates,
        )