def _convert_raw_response_to_dict(
    raw_response: Any,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Safely convert raw_response to dictionary format for conversation history.
    Handles different response types from different LLM providers.

    For the OpenAI Responses API, the raw_response is the entire Response
    object.  Its ``output`` items (messages, function_calls) are extracted
    individually so they can be used as valid input items on the next call.
    Returns a **list** of dicts in that case.

    For Chat Completions / Anthropic / Ollama, returns a single dict.
    """
    if isinstance(raw_response, str):
        # Ollama returns a string, convert to dict format
        return {"role": "assistant", "content": raw_response}
    elif isinstance(raw_response, dict):
        # Already a dict (from tests or some providers)
        return raw_response
    elif _is_responses_api_object(raw_response):
        # OpenAI Responses API: extract individual output items.
        # Strip 'status' — it's a response-only field that OpenAI rejects
        # when the item is sent back as input on the next API call.
        items = [
            {k: v for k, v in json.to_dict(item).items() if k != "status"}
            for item in raw_response.output
        ]
        return items if items else [{"role": "assistant", "content": ""}]
    else:
        # Chat Completions / Anthropic return message objects
        return json.to_dict(raw_response)