async def run_agent(message: str) -> str:
    # Session management for conversation state
    user_id, session_id = "demo_user", "demo_session"
    session_service = runner.session_service

    # Get or create session (required for ADK)
    session = await session_service.get_session(app_name="plugin_demo_app", user_id=user_id, session_id=session_id)
    if not session:
        session = await session_service.create_session(app_name="plugin_demo_app", user_id=user_id, session_id=session_id)

    # Create user message content
    user_content = types.Content(role='user', parts=[types.Part(text=message)])

    # Run agent and collect response - plugin callbacks will fire automatically
    response_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    return response_text if response_text else "No response received from agent."