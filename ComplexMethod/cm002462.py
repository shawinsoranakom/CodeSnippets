def _get_padding_truncation_strategies(
        self, padding=False, truncation=None, max_length=None, pad_to_multiple_of=None, verbose=True, **kwargs
    ):
        """
        Find the correct padding/truncation strategy
        """

        # Backward compatibility for previous behavior:
        # If you only set max_length, it activates truncation for max_length
        if max_length is not None and padding is False and truncation is None:
            truncation = "longest_first"

        # Get padding strategy
        if padding is not False:
            if padding is True:
                if verbose:
                    if max_length is not None and (
                        truncation is None or truncation is False or truncation == "do_not_truncate"
                    ):
                        warnings.warn(
                            "`max_length` is ignored when `padding`=`True` and there is no truncation strategy. "
                            "To pad to max length, use `padding='max_length'`."
                        )
                padding_strategy = PaddingStrategy.LONGEST  # Default to pad to the longest sequence in the batch
            elif not isinstance(padding, PaddingStrategy):
                padding_strategy = PaddingStrategy(padding)
            elif isinstance(padding, PaddingStrategy):
                padding_strategy = padding
        else:
            padding_strategy = PaddingStrategy.DO_NOT_PAD

        # Get truncation strategy
        if truncation is not False and truncation is not None:
            if truncation is True:
                truncation_strategy = (
                    TruncationStrategy.LONGEST_FIRST
                )  # Default to truncate the longest sequences in pairs of inputs
            elif not isinstance(truncation, TruncationStrategy):
                truncation_strategy = TruncationStrategy(truncation)
            elif isinstance(truncation, TruncationStrategy):
                truncation_strategy = truncation
        else:
            truncation_strategy = TruncationStrategy.DO_NOT_TRUNCATE

        # Set max length if needed
        if max_length is None:
            if padding_strategy == PaddingStrategy.MAX_LENGTH:
                if self.model_max_length > LARGE_INTEGER:
                    padding_strategy = PaddingStrategy.DO_NOT_PAD
                else:
                    max_length = self.model_max_length

            if truncation_strategy != TruncationStrategy.DO_NOT_TRUNCATE:
                if self.model_max_length > LARGE_INTEGER:
                    truncation_strategy = TruncationStrategy.DO_NOT_TRUNCATE
                else:
                    max_length = self.model_max_length

        # Test if we have a padding token
        if padding_strategy != PaddingStrategy.DO_NOT_PAD and (self.pad_token is None or self.pad_token_id < 0):
            raise ValueError(
                "Asking to pad but the tokenizer does not have a padding token. "
                "Please select a token to use as `pad_token` `(tokenizer.pad_token = tokenizer.eos_token e.g.)` "
                "or add a new pad token via `tokenizer.add_special_tokens({'pad_token': '[PAD]'})`."
            )

        # Check that we will truncate to a multiple of pad_to_multiple_of if both are provided
        if (
            truncation_strategy != TruncationStrategy.DO_NOT_TRUNCATE
            and padding_strategy != PaddingStrategy.DO_NOT_PAD
            and pad_to_multiple_of is not None
            and max_length is not None
            and (max_length % pad_to_multiple_of != 0)
        ):
            raise ValueError(
                "Truncation and padding are both activated but "
                f"truncation length ({max_length}) is not a multiple of pad_to_multiple_of ({pad_to_multiple_of})."
            )

        return padding_strategy, truncation_strategy, max_length, kwargs