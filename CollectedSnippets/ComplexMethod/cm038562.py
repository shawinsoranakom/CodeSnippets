def _adjust_params_for_parsing(
        self, params: Sequence[SamplingParams | PoolingParams]
    ) -> None:
        """Set ``skip_special_tokens=False`` when the model encodes
        structured output syntax as special tokens.

        Models like Gemma4 register thinking delimiters
        (``<|channel>``/``<channel|>``) and tool call tokens
        (``<|tool_call>``/``<tool_call|>``/``<|"|>``) as special tokens.
        The default ``skip_special_tokens=True`` strips them from
        ``output.text``, breaking parsing of both reasoning blocks and
        tool calls.

        This is a no-op for models whose structured tokens are regular
        text tokens (e.g. DeepSeek's ``<think>``/``</think>``).
        """
        # The offline API currently lacks a unified rendering pipeline.
        # Until the planned Renderer refactor is complete, we hardcode
        # this token preservation logic specifically for Gemma4 models
        # to avoid regressions on other models.
        hf_config = getattr(self.model_config, "hf_config", None)
        architectures = getattr(hf_config, "architectures", [])

        if any("Gemma4" in arch for arch in architectures):
            tokenizer = self.renderer.get_tokenizer()
            vocab = tokenizer.get_vocab()
            special_ids = set(getattr(tokenizer, "all_special_ids", []))

            # Tokens used for thinking delimiters and tool call syntax
            # that some models (Gemma4) register as special tokens.
            structured_tokens = (
                "<|channel>",
                "<channel|>",  # thinking delimiters
                "<|tool_call>",
                "<tool_call|>",  # tool call delimiters
                '<|"|>',  # string quoting in tool args
            )
            needs_special = any(
                vocab.get(tok) in special_ids
                for tok in structured_tokens
                if tok in vocab
            )
            if needs_special:
                for sp in params:
                    if isinstance(sp, SamplingParams) and sp.skip_special_tokens:
                        sp.skip_special_tokens = False