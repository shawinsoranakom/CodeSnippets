def __init__(
        self,
        probs: Tensor | None = None,
        logits: Tensor | None = None,
        validate_args: bool | None = None,
    ) -> None:
        if (probs is None) == (logits is None):
            raise ValueError(
                "Either `probs` or `logits` must be specified, but not both."
            )
        if probs is not None:
            if probs.dim() < 1:
                raise ValueError("`probs` parameter must be at least one-dimensional.")
            # pyrefly: ignore [read-only]
            self.probs = probs / probs.sum(-1, keepdim=True)
        else:
            if logits is None:
                raise AssertionError("logits is unexpectedly None")
            if logits.dim() < 1:
                raise ValueError("`logits` parameter must be at least one-dimensional.")
            # Normalize
            # pyrefly: ignore [read-only]
            self.logits = logits - logits.logsumexp(dim=-1, keepdim=True)
        self._param = self.probs if probs is not None else self.logits
        self._num_events = self._param.size()[-1]
        batch_shape = (
            self._param.size()[:-1] if self._param.ndimension() > 1 else torch.Size()
        )
        # pyrefly: ignore [bad-argument-type]
        super().__init__(batch_shape, validate_args=validate_args)