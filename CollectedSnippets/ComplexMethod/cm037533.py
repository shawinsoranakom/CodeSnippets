def call_hf_processor(
        self,
        hf_processor: Callable[..., BatchFeature] | ProcessorMixin,
        data: Mapping[str, object],
        kwargs: Mapping[str, object] = {},
        *,
        num_tries: int = 1,
        max_tries: int = 5,
    ) -> BatchFeature:
        """
        Call `hf_processor` on the prompt `data`
        (text, image, audio...) with configurable options `kwargs`.
        """
        assert callable(hf_processor)

        merged_kwargs = self.get_merged_mm_kwargs(kwargs)

        allowed_kwargs = get_allowed_kwarg_only_overrides(
            hf_processor,
            merged_kwargs,
            requires_kw_only=False,
            allow_var_kwargs=True,
        )
        allowed_kwargs.setdefault("return_tensors", "pt")

        try:
            output = hf_processor(**data, **allowed_kwargs)
        except Exception as exc:
            # See https://github.com/huggingface/tokenizers/issues/537
            if (
                isinstance(exc, RuntimeError)
                and exc
                and exc.args[0] == "Already borrowed"
                and num_tries < max_tries
            ):
                logger.warning(
                    "Failed to acquire tokenizer in current thread. "
                    "Retrying (%d/%d)...",
                    num_tries,
                    max_tries,
                )
                time.sleep(0.5)
                return self.call_hf_processor(
                    hf_processor,
                    data,
                    kwargs,
                    num_tries=num_tries + 1,
                    max_tries=max_tries,
                )

            msg = (
                f"Failed to apply {type(hf_processor).__name__} "
                f"on data={data} with kwargs={allowed_kwargs}"
            )

            raise ValueError(msg) from exc

        # this emulates output.to(dtype=self.model_config.dtype)
        from transformers.feature_extraction_utils import BatchFeature

        if isinstance(output, BatchFeature):
            output_ = self._postprocess_output(output.data)
            return BatchFeature(output_)  # type: ignore

        logger.warning_once(
            "%s did not return `BatchFeature`. "
            "Make sure to match the behaviour of `ProcessorMixin` when "
            "implementing custom processors.",
            type(hf_processor).__name__,
        )

        return self._postprocess_output(output)