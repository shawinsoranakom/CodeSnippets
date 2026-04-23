def set_truncation_and_padding(
        self,
        padding_strategy,
        truncation_strategy,
        max_length,
        stride,
        pad_to_multiple_of,
    ):
        _truncation = self.tokenizer.truncation
        _padding = self.tokenizer.padding
        # Set truncation and padding on the backend tokenizer
        if truncation_strategy == TruncationStrategy.DO_NOT_TRUNCATE:
            if _truncation is not None:
                self._tokenizer.no_truncation()
        else:
            target = {
                "max_length": max_length,
                "stride": stride,
                "strategy": truncation_strategy.value,
                "direction": "right",
            }

            if _truncation is None:
                current = None
            else:
                current = {k: _truncation.get(k, None) for k in target}

            if current != target:
                self.tokenizer.enable_truncation(**target)
        if padding_strategy == PaddingStrategy.DO_NOT_PAD:
            if _padding is not None:
                self.tokenizer.no_padding()
        else:
            length = (
                max_length if padding_strategy == PaddingStrategy.MAX_LENGTH else None
            )
            target = {
                "length": length,
                "direction": self.padding_side,
                "pad_id": self.pad_token_id,
                "pad_token": self.pad_token,
                "pad_type_id": self.pad_token_type_id,
                "pad_to_multiple_of": pad_to_multiple_of,
            }
            if _padding != target:
                self.tokenizer.enable_padding(**target)