def __init__(
        self,
        probs: Tensor | Number | None = None,
        logits: Tensor | Number | None = None,
        lims: tuple[float, float] = (0.499, 0.501),
        validate_args: bool | None = None,
    ) -> None:
        if (probs is None) == (logits is None):
            raise ValueError(
                "Either `probs` or `logits` must be specified, but not both."
            )
        if probs is not None:
            is_scalar = isinstance(probs, _Number)
            # pyrefly: ignore [read-only]
            (self.probs,) = broadcast_all(probs)
            # validate 'probs' here if necessary as it is later clamped for numerical stability
            # close to 0 and 1, later on; otherwise the clamped 'probs' would always pass
            if validate_args is not None:
                if not self.arg_constraints["probs"].check(self.probs).all():
                    raise ValueError("The parameter probs has invalid values")
            # pyrefly: ignore [read-only]
            self.probs = clamp_probs(self.probs)
        else:
            if logits is None:
                raise AssertionError("logits is unexpectedly None")
            is_scalar = isinstance(logits, _Number)
            # pyrefly: ignore [read-only]
            (self.logits,) = broadcast_all(logits)
        self._param = self.probs if probs is not None else self.logits
        if is_scalar:
            batch_shape = torch.Size()
        else:
            batch_shape = self._param.size()
        self._lims = lims
        super().__init__(batch_shape, validate_args=validate_args)