def _parse_enc_prompt(prompt: PromptType | object) -> EncoderDictPrompt:
    if isinstance(prompt, str):
        return TextPrompt(prompt=prompt)

    if isinstance(prompt, list):
        if not is_list_of(prompt, int):
            raise TypeError("Token prompt should be a list of integers")

        return TokensPrompt(prompt_token_ids=prompt)

    if isinstance(prompt, dict):
        _validate_prompt_dict(prompt)

        if "prompt_embeds" in prompt:
            raise TypeError("Cannot pass embeddings prompt to encoder-decoder models")

        if "prompt" in prompt or "prompt_token_ids" in prompt:
            return prompt  # type: ignore[return-value]

        raise TypeError("Prompt dictionary must contain text or tokens")

    raise TypeError("Prompt should be a string, list of tokens, or dictionary")