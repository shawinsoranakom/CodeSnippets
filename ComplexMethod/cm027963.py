async def analyze_business_intelligence(user_id: str, business_topic: str) -> str:
    """Process business intelligence through the sequential pipeline"""
    session_id = f"bi_session_{user_id}"

    # Support both sync and async session service
    async def _maybe_await(value):
        return await value if inspect.isawaitable(value) else value

    session = await _maybe_await(session_service.get_session(
        app_name="business_intelligence",
        user_id=user_id,
        session_id=session_id
    ))
    if not session:
        session = await _maybe_await(session_service.create_session(
            app_name="business_intelligence",
            user_id=user_id,
            session_id=session_id,
            state={"business_topic": business_topic, "conversation_history": []}
        ))

    # Create user content
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f"Please analyze this business topic: {business_topic}")]
    )

    # Run the sequential pipeline (support async or sync stream)
    response_text = ""
    stream = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content
    )
    if inspect.isasyncgen(stream):
        async for event in stream:
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
    else:
        for event in stream:
            if getattr(event, "is_final_response", lambda: False)():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text

    return response_text