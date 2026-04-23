def __post_init__(self) -> None:
        # Handle deprecated logit_bias → logit_mean
        if self.logit_bias is not None:
            if self.logit_mean is not None:
                raise ValueError(
                    "Cannot set both `logit_bias` and `logit_mean`. "
                    "`logit_bias` is deprecated, use `logit_mean` instead."
                )
            logger.warning(
                "`logit_bias` is deprecated and will be removed in v0.21. "
                "Use `logit_mean` instead."
            )
            self.logit_mean = self.logit_bias
            self.logit_bias = None

        # Handle deprecated logit_scale → logit_sigma
        if self.logit_scale is not None:
            if self.logit_sigma is not None:
                raise ValueError(
                    "Cannot set both `logit_scale` and `logit_sigma`. "
                    "`logit_scale` is deprecated, use `logit_sigma` instead."
                )
            logger.warning(
                "`logit_scale` is deprecated and will be removed in v0.21. "
                "Use `logit_sigma` instead (logit_sigma = 1/logit_scale)."
            )
            if self.logit_scale == 0:
                raise ValueError("logit_scale cannot be 0 (division by zero)")
            self.logit_sigma = 1.0 / self.logit_scale
            self.logit_scale = None

        if self.logit_sigma is not None and self.logit_sigma == 0:
            raise ValueError("logit_sigma cannot be 0 (division by zero)")

        if pooling_type := self.pooling_type:
            if self.seq_pooling_type is not None:
                raise ValueError(
                    "Cannot set both `pooling_type` and `seq_pooling_type`"
                )
            if self.tok_pooling_type is not None:
                raise ValueError(
                    "Cannot set both `pooling_type` and `tok_pooling_type`"
                )

            if pooling_type in SEQ_POOLING_TYPES:
                logger.debug(
                    "Resolved `pooling_type=%r` to `seq_pooling_type=%r`.",
                    pooling_type,
                    pooling_type,
                )
                self.seq_pooling_type = pooling_type  # type: ignore[assignment]
            elif pooling_type in TOK_POOLING_TYPES:
                logger.debug(
                    "Resolved `pooling_type=%r` to `tok_pooling_type=%r`.",
                    pooling_type,
                    pooling_type,
                )
                self.tok_pooling_type = pooling_type  # type: ignore[assignment]
            else:
                raise NotImplementedError(pooling_type)