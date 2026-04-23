def resolve_execution_message(execution_input: str | dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(execution_input, str):
        if not execution_input.strip():
            msg = "Agent execution input message must not be empty."
            raise ValueError(msg)
        return {"role": "user", "content": execution_input}

    if isinstance(execution_input, dict):
        if "role" in execution_input and "content" in execution_input:
            return execution_input

        if "message" in execution_input and isinstance(execution_input["message"], dict):
            return execution_input["message"]

        content = execution_input.get("content")
        if isinstance(content, str) and content.strip():
            return {"role": "user", "content": content}

    msg = (
        "Agent execution requires input content. Provide a non-empty string input "
        "or a message payload with 'role' and 'content'."
    )
    raise ValueError(msg)