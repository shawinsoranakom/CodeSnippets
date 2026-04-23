def to_sampling_params(
        self,
        max_tokens: int,
        default_sampling_params: dict,
    ) -> SamplingParams:
        # Default parameters
        if (repetition_penalty := self.repetition_penalty) is None:
            repetition_penalty = default_sampling_params.get(
                "repetition_penalty",
                self._DEFAULT_SAMPLING_PARAMS["repetition_penalty"],
            )
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
        if (min_p := self.min_p) is None:
            min_p = default_sampling_params.get(
                "min_p", self._DEFAULT_SAMPLING_PARAMS["min_p"]
            )

        prompt_logprobs = self.prompt_logprobs
        if prompt_logprobs is None and self.echo:
            prompt_logprobs = self.top_logprobs

        response_format = self.response_format
        if response_format is not None:
            structured_outputs_kwargs = dict[str, Any]()

            # Set structured output params for response format
            if response_format.type == "json_object":
                structured_outputs_kwargs["json_object"] = True
            elif response_format.type == "json_schema":
                json_schema = response_format.json_schema
                assert json_schema is not None
                structured_outputs_kwargs["json"] = json_schema.json_schema
            elif response_format.type == "structural_tag":
                structural_tag = response_format
                assert structural_tag is not None and isinstance(
                    structural_tag,
                    (
                        LegacyStructuralTagResponseFormat,
                        StructuralTagResponseFormat,
                    ),
                )
                s_tag_obj = structural_tag.model_dump(by_alias=True)
                structured_outputs_kwargs["structural_tag"] = json.dumps(s_tag_obj)

            # If structured outputs wasn't already enabled,
            # we must enable it for these features to work
            if len(structured_outputs_kwargs) > 0:
                self.structured_outputs = (
                    StructuredOutputsParams(**structured_outputs_kwargs)
                    if self.structured_outputs is None
                    else replace(self.structured_outputs, **structured_outputs_kwargs)
                )

        extra_args: dict[str, Any] = self.vllm_xargs if self.vllm_xargs else {}
        if self.kv_transfer_params:
            # Pass in kv_transfer_params via extra_args
            extra_args["kv_transfer_params"] = self.kv_transfer_params
        return SamplingParams.from_optional(
            n=self.n,
            presence_penalty=self.presence_penalty,
            frequency_penalty=self.frequency_penalty,
            repetition_penalty=repetition_penalty,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            min_p=min_p,
            seed=self.seed,
            stop=self.stop,
            stop_token_ids=self.stop_token_ids,
            logprobs=self.top_logprobs if self.logprobs else None,
            prompt_logprobs=prompt_logprobs,
            ignore_eos=self.ignore_eos,
            max_tokens=max_tokens,
            min_tokens=self.min_tokens,
            skip_special_tokens=self.skip_special_tokens,
            spaces_between_special_tokens=self.spaces_between_special_tokens,
            include_stop_str_in_output=self.include_stop_str_in_output,
            output_kind=RequestOutputKind.DELTA
            if self.stream
            else RequestOutputKind.FINAL_ONLY,
            structured_outputs=self.structured_outputs,
            logit_bias=self.logit_bias,
            bad_words=self.bad_words,
            thinking_token_budget=self.thinking_token_budget,
            allowed_token_ids=self.allowed_token_ids,
            extra_args=extra_args or None,
            skip_clone=True,  # Created fresh per request, safe to skip clone
            repetition_detection=self.repetition_detection,
        )