def get_chat_result(
    runnable: LanguageModel,
    input_value: str | Message,
    system_message: str | None = None,
    config: dict | None = None,
    *,
    stream: bool = False,
    token_usage_callback: Callable[[Any], None] | None = None,
):
    if not input_value and not system_message:
        msg = "The message you want to send to the model is empty."
        raise ValueError(msg)

    messages, runnable = build_messages_and_runnable(
        input_value=input_value, system_message=system_message, original_runnable=runnable
    )

    inputs: list | dict = messages or {}
    try:
        if config and config.get("output_parser") is not None:
            runnable |= config["output_parser"]

        if config:
            runnable = runnable.with_config(
                {
                    "run_name": config.get("display_name", ""),
                    "project_name": config.get("get_project_name", lambda: "")(),
                    "callbacks": config.get("get_langchain_callbacks", list)(),
                }
            )
        if stream:
            return runnable.stream(inputs)
        message = runnable.invoke(inputs)
        if token_usage_callback is not None and hasattr(message, "content"):
            token_usage_callback(message)
        return message.content if hasattr(message, "content") else message
    except Exception as e:
        if config and config.get("_get_exception_message") and (message := config["_get_exception_message"](e)):
            raise ValueError(message) from e
        raise