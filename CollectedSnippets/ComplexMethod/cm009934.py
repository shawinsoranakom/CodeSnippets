def _run_llm(
    llm: BaseLanguageModel,
    inputs: dict[str, Any],
    callbacks: Callbacks,
    *,
    tags: list[str] | None = None,
    input_mapper: Callable[[dict], Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> str | BaseMessage:
    """Run the language model on the example.

    Args:
        llm: The language model to run.
        inputs: The input dictionary.
        callbacks: The callbacks to use during the run.
        tags: Optional tags to add to the run.
        input_mapper: function to map to the inputs dictionary from an Example
        metadata: Optional metadata to add to the run.

    Returns:
        The LLMResult or ChatResult.

    Raises:
        ValueError: If the LLM type is unsupported.
        InputFormatError: If the input format is invalid.
    """
    # Most of this is legacy code; we could probably remove a lot of it.
    if input_mapper is not None:
        prompt_or_messages = input_mapper(inputs)
        if isinstance(prompt_or_messages, str) or (
            isinstance(prompt_or_messages, list)
            and all(isinstance(msg, BaseMessage) for msg in prompt_or_messages)
        ):
            llm_output: str | BaseMessage = llm.invoke(
                prompt_or_messages,
                config=RunnableConfig(
                    callbacks=callbacks,
                    tags=tags or [],
                    metadata=metadata or {},
                ),
            )
        else:
            msg = (
                "Input mapper returned invalid format: "
                f" {prompt_or_messages}"
                "\nExpected a single string or list of chat messages."
            )
            raise InputFormatError(msg)
    else:
        try:
            llm_prompts = _get_prompt(inputs)
            llm_output = llm.invoke(
                llm_prompts,
                config=RunnableConfig(
                    callbacks=callbacks,
                    tags=tags or [],
                    metadata=metadata or {},
                ),
            )
        except InputFormatError:
            llm_inputs = _get_messages(inputs)
            llm_output = llm.invoke(
                **llm_inputs,
                config=RunnableConfig(callbacks=callbacks, metadata=metadata or {}),
            )
    return llm_output