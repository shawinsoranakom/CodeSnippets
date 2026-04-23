async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        query: str = "",
        limit: int = 15,
        scope: str = "",
        **kwargs,
    ) -> ToolResponseBase:
        if not user_id:
            return ErrorResponse(
                message="Authentication required to search memories.",
                session_id=session.session_id,
            )

        if not await is_enabled_for_user(user_id):
            return ErrorResponse(
                message="Memory features are not enabled for your account.",
                session_id=session.session_id,
            )

        if not query:
            return ErrorResponse(
                message="A search query is required.",
                session_id=session.session_id,
            )

        limit = min(limit, _MAX_LIMIT)

        try:
            group_id = derive_group_id(user_id)
        except ValueError:
            return ErrorResponse(
                message="Invalid user ID for memory operations.",
                session_id=session.session_id,
            )

        try:
            client = await get_graphiti_client(group_id)

            edges, episodes = await asyncio.gather(
                client.search(
                    query=query,
                    group_ids=[group_id],
                    num_results=limit,
                ),
                client.retrieve_episodes(
                    reference_time=datetime.now(timezone.utc),
                    group_ids=[group_id],
                    last_n=5,
                ),
            )
        except Exception:
            logger.warning(
                "Memory search failed for user %s", user_id[:12], exc_info=True
            )
            return ErrorResponse(
                message="Memory search is temporarily unavailable.",
                session_id=session.session_id,
            )

        facts = _format_edges(edges)

        # Scope hard-filter: if a scope was requested, filter episodes
        # whose MemoryEnvelope JSON contains a different scope.
        # Skip redundant _format_episodes() when scope is set.
        if scope:
            recent = _filter_episodes_by_scope(episodes, scope)
        else:
            recent = _format_episodes(episodes)

        if not facts and not recent:
            return MemorySearchResponse(
                message="No memories found matching your query.",
                session_id=session.session_id,
                facts=[],
                recent_episodes=[],
            )

        scope_note = f" (scope filter: {scope})" if scope else ""
        return MemorySearchResponse(
            message=(
                f"Found {len(facts)} relationship facts and {len(recent)} stored memories{scope_note}. "
                "Use BOTH sections to answer — stored memories often contain operational "
                "rules and instructions that relationship facts summarize."
            ),
            session_id=session.session_id,
            facts=facts,
            recent_episodes=recent,
        )