def before_model_callback(callback_context: CallbackContext, llm_request) -> Optional[types.Content]:
    """Callback before LLM request is made"""
    agent_name = callback_context.agent_name
    request_time = datetime.now()

    # Extract model and prompt from llm_request
    model = getattr(llm_request, 'model', 'unknown')

    # Extract full prompt text from llm_request contents
    prompt_text = "unknown"
    if hasattr(llm_request, 'contents') and llm_request.contents:
        for content in llm_request.contents:
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        prompt_text = part.text
                        break
                if prompt_text != "unknown":
                    break

    print(f"🤖 LLM Request to {model}")
    print(f"⏰ Request time: {request_time.strftime('%H:%M:%S')}")
    print(f"📋 Agent: {agent_name}")
    print()  # Add spacing

    # Store request info in state for after callback
    current_state = callback_context.state.to_dict()
    current_state["llm_request_time"] = request_time.isoformat()
    current_state["llm_model"] = model
    current_state["llm_prompt_length"] = len(prompt_text)
    callback_context.state.update(current_state)

    # Return None to allow normal execution
    return None