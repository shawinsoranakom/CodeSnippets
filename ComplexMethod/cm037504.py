def with_kwargs(self, **tokenization_kwargs: Any):
        max_length = tokenization_kwargs.pop("max_length", self.max_input_tokens)
        pad_prompt_tokens = tokenization_kwargs.pop(
            "pad_prompt_tokens", self.pad_prompt_tokens
        )
        truncate_prompt_tokens = tokenization_kwargs.pop(
            "truncate_prompt_tokens", self.truncate_prompt_tokens
        )
        do_lower_case = tokenization_kwargs.pop("do_lower_case", self.do_lower_case)
        add_special_tokens = tokenization_kwargs.pop(
            "add_special_tokens", self.add_special_tokens
        )
        needs_detokenization = tokenization_kwargs.pop(
            "needs_detokenization", self.needs_detokenization
        )

        # https://huggingface.co/docs/transformers/en/pad_truncation
        if padding := tokenization_kwargs.pop("padding", None):
            if padding == "max_length":
                pad_prompt_tokens = max_length
            elif padding in (False, "do_not_pad"):
                pad_prompt_tokens = None
            else:
                # To emit the below warning
                tokenization_kwargs["padding"] = padding

        if truncation := tokenization_kwargs.pop("truncation", None):
            if truncation in (True, "longest_first"):
                truncate_prompt_tokens = max_length
            elif truncation in (False, "do_not_truncate"):
                truncate_prompt_tokens = None
            else:
                # To emit the below warning
                tokenization_kwargs["truncation"] = truncation

        if tokenization_kwargs:
            logger.warning(
                "The following tokenization arguments are not supported "
                "by vLLM Renderer and will be ignored: %s",
                tokenization_kwargs,
            )

        max_total_tokens = self.max_total_tokens

        return TokenizeParams(
            max_total_tokens=max_total_tokens,
            max_output_tokens=(
                0
                if max_total_tokens is None or max_length is None
                else max_total_tokens - max_length
            ),
            pad_prompt_tokens=pad_prompt_tokens,
            truncate_prompt_tokens=truncate_prompt_tokens,
            truncation_side=self.truncation_side,
            do_lower_case=do_lower_case,
            add_special_tokens=add_special_tokens,
            needs_detokenization=needs_detokenization,
        )