def _validate_model_input(
        self,
        prompt_input: SingletonInput,
        prompt_type: Literal["encoder", "decoder"],
    ) -> None:
        model_config = self.model_config
        tokenizer = self.tokenizer

        prompt_ids = (
            None
            if prompt_input["type"] == "embeds"
            else prompt_input["prompt_token_ids"]
        )
        prompt_embeds = (
            prompt_input["prompt_embeds"] if prompt_input["type"] == "embeds" else None
        )

        prompt_len = length_from_prompt_token_ids_or_embeds(prompt_ids, prompt_embeds)
        self._validate_prompt_len(prompt_len, prompt_type)

        if prompt_input["type"] == "multimodal":
            decoder_mm_positions = prompt_input["mm_placeholders"]
            for modality, mm_positions in decoder_mm_positions.items():
                for mm_position in mm_positions:
                    num_embeds = mm_position.get_num_embeds()
                    if num_embeds > self.mm_encoder_cache_size:
                        raise ValueError(
                            f"The {prompt_type} prompt contains a(n) {modality} item "
                            f"with {num_embeds} embedding tokens, which exceeds the "
                            f"pre-allocated encoder cache size "
                            f"{self.mm_encoder_cache_size}. Please reduce the input "
                            f"size or increase the encoder cache size "
                            f"by setting --limit-mm-per-prompt at startup."
                        )

        if prompt_ids and tokenizer is not None:
            max_input_id = max(prompt_ids, default=0)

            # NOTE: tokenizer.max_token_id is the tokenizer’s vocab size while
            # self.model_config.get_vocab_size() is the model’s vocab size.
            # For Qwen3 models, the language model has extra tokens that do
            # not exist in the tokenizer, and vice versa for multimodal
            # placeholder tokens in some multimodal models.
            # See https://github.com/QwenLM/Qwen3/issues/29#issuecomment-1933720399 # noqa: E501
            # and https://github.com/vllm-project/vllm/pull/22471#discussion_r2312251421 # noqa: E501

            # Here we take the max of the two to determine if a token id is
            # truly out-of-vocabulary.
            model_vocab_size = model_config.get_vocab_size()
            if max_input_id > max(tokenizer.max_token_id, model_vocab_size - 1):
                raise ValueError(f"Token id {max_input_id} is out of vocabulary")