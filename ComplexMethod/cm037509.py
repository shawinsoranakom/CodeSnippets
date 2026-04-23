def _parse_dec_prompt(prompt: PromptType | object) -> DecoderDictPrompt:
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

        if (
            "multi_modal_data" in prompt
            or "mm_processor_kwargs" in prompt
            or "multi_modal_uuids" in prompt
        ):
            raise TypeError("Cannot pass multi-modal inputs to decoder prompt")

        if "prompt" in prompt or "prompt_token_ids" in prompt:
            return prompt  # type: ignore[return-value]

        raise TypeError("Prompt dictionary must contain text or tokens")

    raise TypeError("Prompt should be a string, list of tokens, or dictionary")