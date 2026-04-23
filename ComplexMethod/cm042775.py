def get_prompt_style(
    prompt_style: (
        Literal["default", "llama2", "llama3", "tag", "mistral", "chatml"] | None
    )
) -> AbstractPromptStyle:
    """Get the prompt style to use from the given string.

    :param prompt_style: The prompt style to use.
    :return: The prompt style to use.
    """
    if prompt_style is None or prompt_style == "default":
        return DefaultPromptStyle()
    elif prompt_style == "llama2":
        return Llama2PromptStyle()
    elif prompt_style == "llama3":
        return Llama3PromptStyle()
    elif prompt_style == "tag":
        return TagPromptStyle()
    elif prompt_style == "mistral":
        return MistralPromptStyle()
    elif prompt_style == "chatml":
        return ChatMLPromptStyle()
    raise ValueError(f"Unknown prompt_style='{prompt_style}'")