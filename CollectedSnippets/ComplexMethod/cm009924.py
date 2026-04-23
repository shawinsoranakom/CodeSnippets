def _get_prompt(inputs: dict[str, Any]) -> str:
    """Get prompt from inputs.

    Args:
        inputs: The input dictionary.

    Returns:
        A string prompt.

    Raises:
        InputFormatError: If the input format is invalid.
    """
    if not inputs:
        msg = "Inputs should not be empty."
        raise InputFormatError(msg)

    prompts = []
    if "prompt" in inputs:
        if not isinstance(inputs["prompt"], str):
            msg = f"Expected string for 'prompt', got {type(inputs['prompt']).__name__}"
            raise InputFormatError(msg)
        prompts = [inputs["prompt"]]
    elif "prompts" in inputs:
        if not isinstance(inputs["prompts"], list) or not all(
            isinstance(i, str) for i in inputs["prompts"]
        ):
            msg = (
                "Expected list of strings for 'prompts',"
                f" got {type(inputs['prompts']).__name__}"
            )
            raise InputFormatError(msg)
        prompts = inputs["prompts"]
    elif len(inputs) == 1:
        prompt_ = next(iter(inputs.values()))
        if isinstance(prompt_, str):
            prompts = [prompt_]
        elif isinstance(prompt_, list) and all(isinstance(i, str) for i in prompt_):
            prompts = prompt_
        else:
            msg = f"LLM Run expects string prompt input. Got {inputs}"
            raise InputFormatError(msg)
    else:
        msg = f"LLM Run expects 'prompt' or 'prompts' in inputs. Got {inputs}"
        raise InputFormatError(msg)
    if len(prompts) == 1:
        return prompts[0]
    msg = f"LLM Run expects single prompt input. Got {len(prompts)} prompts."
    raise InputFormatError(msg)