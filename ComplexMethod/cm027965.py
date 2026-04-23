async def iterate_spec_until_acceptance(
    user_id: str, topic: str, target_iterations: int = 3
) -> Dict[str, Any]:
    """Run the LoopAgent to iteratively refine a plan.

    Returns a dictionary with final plan text and iteration metadata.
    """
    session_id = f"loop_refinement_{user_id}"

    async def _maybe_await(value):
        return await value if inspect.isawaitable(value) else value

    # Create or get session (support both sync/async services)
    session = await _maybe_await(session_service.get_session(
        app_name="loop_refinement_app",
        user_id=user_id,
        session_id=session_id,
    ))
    if not session:
        session = await _maybe_await(session_service.create_session(
            app_name="loop_refinement_app",
            user_id=user_id,
            session_id=session_id,
            state={
                "topic": topic,
                "iteration": 0,
                "target_iterations": int(target_iterations),
                # Optionally, an external process or UI could set this to True to stop early
                "accepted": False,
            },
        ))
    else:
        # Refresh topic/target if user re-runs on UI
        if hasattr(session, "state") and isinstance(session.state, dict):
            session.state["topic"] = topic
            session.state["target_iterations"] = int(target_iterations)

    # Seed message for LLM
    user_content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "Topic: "
                    + topic
                    + "\nPlease produce or refine a concise plan."
                )
            )
        ],
    )

    final_text = ""
    last_plan_text = ""
    stream = runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content)
    # Support both async generators and plain iterables
    if inspect.isasyncgen(stream):
        async for event in stream:
            if event.content and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        # Keep last text from plan_refiner preferentially
                        if getattr(event, "author", "") == plan_refiner.name:
                            last_plan_text = part.text
                        if event.is_final_response():
                            final_text = part.text
    else:
        for event in stream:
            if event.content and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        if getattr(event, "author", "") == plan_refiner.name:
                            last_plan_text = part.text
                        # final events in sync mode
                        final_text = part.text
        if event.content and getattr(event.content, "parts", None):
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    # Keep last text from plan_refiner preferentially
                    if getattr(event, "author", "") == plan_refiner.name:
                        last_plan_text = part.text
                    if event.is_final_response():
                        final_text = part.text

    current_iteration = int(session.state.get("iteration", 0))
    reached = current_iteration >= int(session.state.get("target_iterations", 0))
    accepted = bool(session.state.get("accepted", False))

    return {
        "final_plan": last_plan_text or final_text,
        "iterations": current_iteration,
        "stopped_reason": "accepted" if accepted else ("target_iterations" if reached else "max_iterations_or_other"),
    }