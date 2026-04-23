def __init__(
        self,
        probs: Tensor | Number | None = None,
        logits: Tensor | Number | None = None,
        validate_args: bool | None = None,
    ) -> None:
        if (probs is None) == (logits is None):
            raise ValueError(
                "Either `probs` or `logits` must be specified, but not both."
            )
        if probs is not None:
            # pyrefly: ignore [read-only]
            (self.probs,) = broadcast_all(probs)
        else:
            if logits is None:
                raise AssertionError("logits is unexpectedly None")
            # pyrefly: ignore [read-only]
            (self.logits,) = broadcast_all(logits)
        probs_or_logits = probs if probs is not None else logits
        if isinstance(probs_or_logits, _Number):
            batch_shape = torch.Size()
        else:
            if probs_or_logits is None:
                raise AssertionError("probs_or_logits is unexpectedly None")
            batch_shape = probs_or_logits.size()
        super().__init__(batch_shape, validate_args=validate_args)
        if self._validate_args and probs is not None:
            # Add an extra check beyond unit_interval
            value = self.probs
            valid = value > 0
            if not valid.all():
                invalid_value = value.data[~valid]
                raise ValueError(
                    "Expected parameter probs "
                    f"({type(value).__name__} of shape {tuple(value.shape)}) "
                    f"of distribution {repr(self)} "
                    f"to be positive but found invalid values:\n{invalid_value}"
                )