def _build_commands(
    model_response: ModelResponse,
    middleware_commands: list[Command[Any]] | None = None,
) -> list[Command[Any]]:
    """Build a list of Commands from a model response and middleware commands.

    The first Command contains the model response state (messages and optional
    structured_response). Middleware commands are appended as-is.

    Args:
        model_response: The model response containing messages and optional
            structured output.
        middleware_commands: Commands accumulated from middleware layers during
            composition (inner-first ordering).

    Returns:
        List of ``Command`` objects ready to be returned from a model node.
    """
    state: dict[str, Any] = {"messages": model_response.result}

    if model_response.structured_response is not None:
        state["structured_response"] = model_response.structured_response

    for cmd in middleware_commands or []:
        if cmd.goto:
            msg = (
                "Command goto is not yet supported in wrap_model_call middleware. "
                "Use the jump_to state field with before_model/after_model hooks instead."
            )
            raise NotImplementedError(msg)
        if cmd.resume:
            msg = "Command resume is not yet supported in wrap_model_call middleware."
            raise NotImplementedError(msg)
        if cmd.graph:
            msg = "Command graph is not yet supported in wrap_model_call middleware."
            raise NotImplementedError(msg)

    commands: list[Command[Any]] = [Command(update=state)]
    commands.extend(middleware_commands or [])
    return commands