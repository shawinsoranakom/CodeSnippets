async def _arun_llm(
    llm: BaseLanguageModel,
    inputs: dict[str, Any],
    *,
    tags: list[str] | None = None,
    callbacks: Callbacks = None,
    input_mapper: Callable[[dict], Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | BaseMessage:
    """Asynchronously run the language model.

    Args:
        llm: The language model to run.
        inputs: The input dictionary.
        tags: Optional tags to add to the run.
        callbacks: Optional callbacks to use during the run.
        input_mapper: Optional function to map inputs to the expected format.
        metadata: Optional metadata to add to the run.

    Returns:
        The LLMResult or ChatResult.

    Raises:
        ValueError: If the LLM type is unsupported.
        InputFormatError: If the input format is invalid.
    """
    if input_mapper is not None:
        prompt_or_messages = input_mapper(inputs)
        if isinstance(prompt_or_messages, str) or (
            isinstance(prompt_or_messages, list)
            and all(isinstance(msg, BaseMessage) for msg in prompt_or_messages)
        ):
            return await llm.ainvoke(
                prompt_or_messages,
                config=RunnableConfig(
                    callbacks=callbacks,
                    tags=tags or [],
                    metadata=metadata or {},
                ),
            )
        msg = (
            "Input mapper returned invalid format"
            f" {prompt_or_messages}"
            "\nExpected a single string or list of chat messages."
        )
        raise InputFormatError(msg)

    try:
        prompt = _get_prompt(inputs)
        llm_output: str | BaseMessage = await llm.ainvoke(
            prompt,
            config=RunnableConfig(
                callbacks=callbacks,
                tags=tags or [],
                metadata=metadata or {},
            ),
        )
    except InputFormatError:
        llm_inputs = _get_messages(inputs)
        llm_output = await llm.ainvoke(
            **llm_inputs,
            config=RunnableConfig(
                callbacks=callbacks,
                tags=tags or [],
                metadata=metadata or {},
            ),
        )
    return llm_output