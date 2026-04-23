def _sanitize_parameters(
        self,
        ignore_labels=None,
        aggregation_strategy: AggregationStrategy | None = None,
        offset_mapping: list[tuple[int, int]] | None = None,
        is_split_into_words: bool = False,
        stride: int | None = None,
        delimiter: str | None = None,
    ):
        preprocess_params = {}
        preprocess_params["is_split_into_words"] = is_split_into_words

        if is_split_into_words:
            preprocess_params["delimiter"] = " " if delimiter is None else delimiter

        if offset_mapping is not None:
            preprocess_params["offset_mapping"] = offset_mapping

        postprocess_params = {}
        if aggregation_strategy is not None:
            if isinstance(aggregation_strategy, str):
                aggregation_strategy = AggregationStrategy[aggregation_strategy.upper()]
            if (
                aggregation_strategy
                in {AggregationStrategy.FIRST, AggregationStrategy.MAX, AggregationStrategy.AVERAGE}
                and not self.tokenizer.is_fast
            ):
                raise ValueError(
                    "Slow tokenizers cannot handle subwords. Please set the `aggregation_strategy` option"
                    ' to `"simple"` or use a fast tokenizer.'
                )
            postprocess_params["aggregation_strategy"] = aggregation_strategy
        if ignore_labels is not None:
            postprocess_params["ignore_labels"] = ignore_labels
        if stride is not None:
            if stride >= self.tokenizer.model_max_length:
                raise ValueError(
                    "`stride` must be less than `tokenizer.model_max_length` (or even lower if the tokenizer adds special tokens)"
                )
            if aggregation_strategy == AggregationStrategy.NONE:
                raise ValueError(
                    "`stride` was provided to process all the text but `aggregation_strategy="
                    f'"{aggregation_strategy}"`, please select another one instead.'
                )
            else:
                if self.tokenizer.is_fast:
                    tokenizer_params = {
                        "return_overflowing_tokens": True,
                        "padding": True,
                        "stride": stride,
                    }
                    preprocess_params["tokenizer_params"] = tokenizer_params
                else:
                    raise ValueError(
                        "`stride` was provided to process all the text but you're using a slow tokenizer."
                        " Please use a fast tokenizer."
                    )
        return preprocess_params, {}, postprocess_params