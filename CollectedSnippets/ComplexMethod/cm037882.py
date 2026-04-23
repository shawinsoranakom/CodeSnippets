def validate_params(cls, params: SamplingParams):
        ngram_size = params.extra_args and params.extra_args.get("ngram_size")
        window_size = params.extra_args and params.extra_args.get("window_size", 100)
        whitelist_token_ids = params.extra_args and params.extra_args.get(
            "whitelist_token_ids", None
        )
        # if ngram_size is not provided, skip validation because the processor
        # will not be used.
        if ngram_size is None:
            return None

        if not isinstance(ngram_size, int) or ngram_size <= 0:
            raise ValueError(
                f"`ngram_size` has to be a strictly positive integer, got {ngram_size}."
            )
        if not isinstance(window_size, int) or window_size <= 0:
            raise ValueError(
                "`window_size` has to be a strictly positive integer, "
                f"got {window_size}."
            )
        if whitelist_token_ids is not None and not isinstance(
            whitelist_token_ids, Iterable
        ):
            raise ValueError(
                "`whitelist_token_ids` has to be a sequence of integers, "
                f"got {whitelist_token_ids}."
            )