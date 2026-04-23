def parse_dec_only_prompt(prompt: PromptType | object) -> DecoderOnlyDictPrompt:
    """
    Parse a prompt for a decoder-only model and normalize it to a dictionary.
    """
    if isinstance(prompt, str):
        return TextPrompt(prompt=prompt)

    if isinstance(prompt, list):
        if not is_list_of(prompt, int):
            raise TypeError("Token prompt should be a list of integers")

        return TokensPrompt(prompt_token_ids=prompt)

    if isinstance(prompt, dict):
        if "encoder_prompt" in prompt:
            raise TypeError("Cannot pass encoder-decoder prompt to decoder-only models")

        _validate_prompt_dict(prompt)

        if (
            "prompt" in prompt
            or "prompt_token_ids" in prompt
            or "prompt_embeds" in prompt
        ):
            return prompt  # type: ignore[return-value]

        raise TypeError("Prompt dictionary must contain text, tokens, or embeddings")

    raise TypeError("Prompt should be a string, list of tokens, or dictionary")