async def gather_market_snapshot(user_id: str, topic: str) -> Dict[str, Any]:
    """Execute the parallel agents and return combined snapshot text blocks.

    Returns keys: 'market_trends', 'competitors', 'funding_news'.
    """
    session_id = f"parallel_snapshot_{user_id}"

    async def _maybe_await(v):
        return await v if inspect.isawaitable(v) else v

    session = await _maybe_await(
        session_service.get_session(
            app_name="parallel_snapshot_app", user_id=user_id, session_id=session_id
        )
    )
    if not session:
        session = await _maybe_await(
            session_service.create_session(
                app_name="parallel_snapshot_app",
                user_id=user_id,
                session_id=session_id,
                state={"topic": topic},
            )
        )
    else:
        if hasattr(session, "state") and isinstance(session.state, dict):
            session.state["topic"] = topic

    user_content = types.Content(
        role="user",
        parts=[types.Part(text=f"Topic: {topic}. Provide a concise snapshot per agent focus.")],
    )

    # Collect last text emitted per agent
    last_text_by_agent: Dict[str, str] = {}

    stream = runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content)
    if inspect.isasyncgen(stream):
        async for event in stream:
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        author = getattr(event, "author", "")
                        if author:
                            last_text_by_agent[author] = part.text
    else:
        for event in stream:
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        author = getattr(event, "author", "")
                        if author:
                            last_text_by_agent[author] = part.text

    return {
        "market_trends": last_text_by_agent.get(market_trends_agent.name, ""),
        "competitors": last_text_by_agent.get(competitor_intel_agent.name, ""),
        "funding_news": last_text_by_agent.get(funding_news_agent.name, ""),
    }