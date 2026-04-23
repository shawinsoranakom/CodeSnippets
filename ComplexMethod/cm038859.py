def get_llm_response(messages, model, reason, content_ph=None, reasoning_ph=None):
    """Generate and stream LLM response with optional reasoning process.

    Args:
        messages (list): List of conversation message dicts with 'role' and 'content'
        model (str): The model identifier to use for generation
        reason (bool): Whether to enable and display reasoning process
        content_ph (streamlit.empty): Placeholder for streaming response content
        reasoning_ph (streamlit.empty): Placeholder for streaming reasoning process

    Returns:
        tuple: (str, str)
            - First string contains the complete response text
            - Second string contains the complete reasoning text (if enabled)

    Features:
        - Streams both reasoning and response text in real-time
        - Handles model API errors gracefully
        - Supports live updating of thinking process
        - Maintains separate content and reasoning displays

    Raises:
        Exception: Wrapped in error message if API call fails

    Note:
        The function uses streamlit placeholders for live updates.
        When reason=True, the reasoning process appears above the response.
    """
    full_text = ""
    think_text = ""
    live_think = None
    # Build request parameters
    params = {"model": model, "messages": messages, "stream": True}
    if reason:
        params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}

    try:
        response = client.chat.completions.create(**params)
        if isinstance(response, str):
            if content_ph:
                content_ph.markdown(response)
            return response, ""

        # Prepare reasoning expander above content
        if reason and reasoning_ph:
            exp = reasoning_ph.expander("💭 Thinking Process (live)", expanded=True)
            live_think = exp.empty()

        # Stream chunks
        for chunk in response:
            delta = chunk.choices[0].delta
            # Stream reasoning first
            if reason and hasattr(delta, "reasoning") and live_think:
                rc = delta.reasoning
                if rc:
                    think_text += rc
                    live_think.markdown(think_text + "▌")
            # Then stream content
            if hasattr(delta, "content") and delta.content and content_ph:
                full_text += delta.content
                content_ph.markdown(full_text + "▌")

        # Finalize displays: reasoning remains above, content below
        if reason and live_think:
            live_think.markdown(think_text)
        if content_ph:
            content_ph.markdown(full_text)

        return full_text, think_text
    except Exception as e:
        st.error(f"Error details: {str(e)}")
        return f"Error: {str(e)}", ""