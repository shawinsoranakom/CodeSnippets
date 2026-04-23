def to_sampling_params(
        self,
        default_max_tokens: int,
        default_sampling_params: dict | None = None,
    ) -> SamplingParams:
        if self.max_output_tokens is None:
            max_tokens = default_max_tokens
        else:
            max_tokens = min(self.max_output_tokens, default_max_tokens)

        default_sampling_params = default_sampling_params or {}
        if (temperature := self.temperature) is None:
            temperature = default_sampling_params.get(
                "temperature", self._DEFAULT_SAMPLING_PARAMS["temperature"]
            )
        if (top_p := self.top_p) is None:
            top_p = default_sampling_params.get(
                "top_p", self._DEFAULT_SAMPLING_PARAMS["top_p"]
            )
        if (top_k := self.top_k) is None:
            top_k = default_sampling_params.get(
                "top_k", self._DEFAULT_SAMPLING_PARAMS["top_k"]
            )

        if (repetition_penalty := self.repetition_penalty) is None:
            repetition_penalty = default_sampling_params.get("repetition_penalty", 1.0)

        if (presence_penalty := self.presence_penalty) is None:
            presence_penalty = default_sampling_params.get("presence_penalty", 0.0)

        if (frequency_penalty := self.frequency_penalty) is None:
            frequency_penalty = default_sampling_params.get("frequency_penalty", 0.0)

        stop_token_ids = default_sampling_params.get("stop_token_ids")

        # Structured output
        structured_outputs = self.structured_outputs

        # Also check text.format for OpenAI-style json_schema
        if self.text is not None and self.text.format is not None:
            if structured_outputs is not None:
                raise VLLMValidationError(
                    "Cannot specify both structured_outputs and text.format",
                    parameter="structured_outputs",
                )
            response_format = self.text.format
            if (
                response_format.type == "json_schema"
                and response_format.schema_ is not None
            ):
                structured_outputs = StructuredOutputsParams(
                    json=response_format.schema_  # type: ignore[call-arg]
                    # --follow-imports skip hides the class definition but also hides
                    # multiple third party conflicts, so best of both evils
                )

        stop = self.stop if self.stop else []
        if isinstance(stop, str):
            stop = [stop]

        extra_args: dict[str, Any] = self.vllm_xargs if self.vllm_xargs else {}
        if self.kv_transfer_params:
            extra_args["kv_transfer_params"] = self.kv_transfer_params

        return SamplingParams.from_optional(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_tokens=max_tokens,
            logprobs=self.top_logprobs if self.is_include_output_logprobs() else None,
            stop_token_ids=stop_token_ids,
            stop=stop,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            seed=self.seed,
            ignore_eos=self.ignore_eos,
            output_kind=(
                RequestOutputKind.DELTA if self.stream else RequestOutputKind.FINAL_ONLY
            ),
            structured_outputs=structured_outputs,
            logit_bias=self.logit_bias,
            extra_args=extra_args,
            skip_clone=True,  # Created fresh per request, safe to skip clone
            skip_special_tokens=self.skip_special_tokens,
            include_stop_str_in_output=self.include_stop_str_in_output,
        )