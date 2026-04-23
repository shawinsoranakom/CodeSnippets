def to_sampling_params(
        self, default_max_tokens: int, default_sampling_params: dict | None = None
    ) -> SamplingParams:
        max_tokens = default_max_tokens

        if default_sampling_params is None:
            default_sampling_params = {}

        # Default parameters
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

        if (repetition_penalty := self.repetition_penalty) is None:
            repetition_penalty = default_sampling_params.get(
                "repetition_penalty",
                self._DEFAULT_SAMPLING_PARAMS["repetition_penalty"],
            )

        return SamplingParams.from_optional(
            temperature=temperature,
            max_tokens=max_tokens,
            seed=self.seed,
            top_p=top_p,
            top_k=top_k,
            min_p=min_p,
            frequency_penalty=self.frequency_penalty,
            repetition_penalty=repetition_penalty,
            presence_penalty=self.presence_penalty,
            output_kind=RequestOutputKind.DELTA
            if self.stream
            else RequestOutputKind.FINAL_ONLY,
            extra_args=self.vllm_xargs,
            skip_clone=True,  # Created fresh per request, safe to skip clone
        )