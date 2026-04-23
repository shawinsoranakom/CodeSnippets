def __init__(
        self,
        df: Tensor | Number,
        covariance_matrix: Tensor | None = None,
        precision_matrix: Tensor | None = None,
        scale_tril: Tensor | None = None,
        validate_args: bool | None = None,
    ) -> None:
        if (
            (covariance_matrix is not None)
            + (scale_tril is not None)
            + (precision_matrix is not None)
        ) != 1:
            raise AssertionError(
                "Exactly one of covariance_matrix or precision_matrix or scale_tril may be specified."
            )

        param = next(
            p
            for p in (covariance_matrix, precision_matrix, scale_tril)
            if p is not None
        )

        if param.dim() < 2:
            raise ValueError(
                "scale_tril must be at least two-dimensional, with optional leading batch dimensions"
            )

        if isinstance(df, _Number):
            batch_shape = torch.Size(param.shape[:-2])
            self.df = torch.tensor(df, dtype=param.dtype, device=param.device)
        else:
            batch_shape = torch.broadcast_shapes(param.shape[:-2], df.shape)
            self.df = df.expand(batch_shape)
        event_shape = param.shape[-2:]

        if self.df.le(event_shape[-1] - 1).any():
            raise ValueError(
                f"Value of df={df} expected to be greater than ndim - 1 = {event_shape[-1] - 1}."
            )

        if scale_tril is not None:
            # pyrefly: ignore [read-only]
            self.scale_tril = param.expand(batch_shape + (-1, -1))
        elif covariance_matrix is not None:
            # pyrefly: ignore [read-only]
            self.covariance_matrix = param.expand(batch_shape + (-1, -1))
        elif precision_matrix is not None:
            # pyrefly: ignore [read-only]
            self.precision_matrix = param.expand(batch_shape + (-1, -1))

        if self.df.lt(event_shape[-1]).any():
            warnings.warn(
                "Low df values detected. Singular samples are highly likely to occur for ndim - 1 < df < ndim.",
                stacklevel=2,
            )

        # pyrefly: ignore [bad-argument-type]
        super().__init__(batch_shape, event_shape, validate_args=validate_args)
        self._batch_dims = [-(x + 1) for x in range(len(self._batch_shape))]

        if scale_tril is not None:
            self._unbroadcasted_scale_tril = scale_tril
        elif covariance_matrix is not None:
            self._unbroadcasted_scale_tril = torch.linalg.cholesky(covariance_matrix)
        else:  # precision_matrix is not None
            self._unbroadcasted_scale_tril = _precision_to_scale_tril(precision_matrix)

        # Chi2 distribution is needed for Bartlett decomposition sampling
        self._dist_chi2 = torch.distributions.chi2.Chi2(
            df=(
                self.df.unsqueeze(-1)
                - torch.arange(
                    self._event_shape[-1],
                    dtype=self._unbroadcasted_scale_tril.dtype,
                    device=self._unbroadcasted_scale_tril.device,
                ).expand(batch_shape + (-1,))
            )
        )