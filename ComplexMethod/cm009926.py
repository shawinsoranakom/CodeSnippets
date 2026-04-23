def _validate_example_inputs_for_language_model(
    first_example: Example,
    input_mapper: Callable[[dict], Any] | None,
) -> None:
    if input_mapper:
        prompt_input = input_mapper(first_example.inputs or {})
        if not isinstance(prompt_input, str) and not (
            isinstance(prompt_input, list)
            and all(isinstance(msg, BaseMessage) for msg in prompt_input)
        ):
            msg = (
                "When using an input_mapper to prepare dataset example inputs"
                " for an LLM or chat model, the output must a single string or"
                " a list of chat messages."
                f"\nGot: {prompt_input} of type {type(prompt_input)}."
            )
            raise InputFormatError(msg)
    else:
        try:
            _get_prompt(first_example.inputs or {})
        except InputFormatError:
            try:
                _get_messages(first_example.inputs or {})
            except InputFormatError as err2:
                msg = (
                    "Example inputs do not match language model input format. "
                    "Expected a dictionary with messages or a single prompt."
                    f" Got: {first_example.inputs}"
                    " Please update your dataset OR provide an input_mapper"
                    " to convert the example.inputs to a compatible format"
                    " for the llm or chat model you wish to evaluate."
                )
                raise InputFormatError(msg) from err2