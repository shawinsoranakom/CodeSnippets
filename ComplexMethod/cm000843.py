async def _generate_session_title(
    message: str,
    user_id: str | None = None,
    session_id: str | None = None,
) -> tuple[str | None, ChatCompletion | None]:
    """Generate a concise title for a chat session based on the first message.

    Returns ``(title, response)``.  The caller is responsible for
    persisting the title AND recording the title call's cost — keeping
    them as separate concerns in the caller lets a cost-tracking hiccup
    not lose the title, and lets a title-persist failure still record
    the cost (we paid for the LLM call either way).

    Args:
        message: The first user message in the session
        user_id: User ID for OpenRouter tracing (optional)
        session_id: Session ID for OpenRouter tracing (optional)

    Returns:
        ``(title, response)`` on success; ``(None, None)`` if the LLM
        call raised.  ``response`` is returned even when ``title`` is
        empty so the caller can still record the (paid-for) cost.
    """
    try:
        # Build extra_body for OpenRouter tracing and PostHog analytics.
        # ``usage: {"include": True}`` asks OR to embed the real billed
        # cost into the final usage chunk — matches the baseline path's
        # ``_OPENROUTER_INCLUDE_USAGE_COST`` pattern, same read path.
        extra_body: dict[str, Any] = {"usage": {"include": True}}
        if user_id:
            extra_body["user"] = user_id[:128]  # OpenRouter limit
            extra_body["posthogDistinctId"] = user_id
        if session_id:
            extra_body["session_id"] = session_id[:128]  # OpenRouter limit
        extra_body["posthogProperties"] = {
            "environment": settings.config.app_env.value,
        }

        response = await _get_openai_client().chat.completions.create(
            model=config.title_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a very short title (3-6 words) for a chat conversation "
                        "based on the user's first message. The title should capture the "
                        "main topic or intent. Return ONLY the title, no quotes or punctuation."
                    ),
                },
                {"role": "user", "content": message[:500]},  # Limit input length
            ],
            max_tokens=20,
            extra_body=extra_body,
        )
    except Exception as e:
        logger.warning(f"Failed to generate session title: {e}")
        return None, None

    # Robust against an empty ``choices`` list OR a choice whose
    # ``message`` is missing ``content`` (shouldn't happen on the OpenAI
    # SDK typing, but belt-and-suspenders — the background task would
    # otherwise die on ``IndexError`` and lose the (paid-for) cost
    # recording we're about to do below).
    title: str | None = None
    if response.choices:
        msg = response.choices[0].message
        title = msg.content if msg is not None else None
    if title:
        title = title.strip().strip("\"'")
        if len(title) > 50:
            title = title[:47] + "..."
    return title, response