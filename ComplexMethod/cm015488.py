def _reduce_scatter_validate_mp(
        self, orig_reduce_scatter, mp_config, should_run_low_prec, *args, **kwargs
    ):
        """
        Runs reduce-scatter but verifies mixed precision settings before. This
        is to test mixed precision is working as expected during backward pass.
        In particular it ensures that the gradients were cast to the right type
        and comm. is going to happen in the right type.
        """
        tensors = []
        for x in args:
            if isinstance(x, torch.Tensor):
                tensors.append(x)
        for x in kwargs.values():
            if isinstance(x, torch.Tensor):
                tensors.append(x)

        # reduce_dtype has higher priority than param_dtype, because mixed_precision
        # supports overriding param_dtype with reduce_dtype to control the
        # reduction precision. In the case where reduce_dtype == param_dtype
        # this tests that gradients are in the expected precision as well.
        # If reduce_dtype is not specified (is None) we comm. in the param_dtype
        # if that is specified, otherwise full precision dtype.
        if should_run_low_prec:
            expected_dtype = (
                mp_config.reduce_dtype
                if mp_config.reduce_dtype is not None
                else (
                    mp_config.param_dtype
                    if mp_config.param_dtype is not None
                    else _CURRENT_FULL_PRECISION_PARAM_DTYPE
                )
            )
        else:
            expected_dtype = _CURRENT_FULL_PRECISION_PARAM_DTYPE

        for t in tensors:
            self.assertEqual(
                expected_dtype,
                t.dtype,
                f"Expected to reduce in {expected_dtype} but got tensors in {t.dtype}",
            )

        return orig_reduce_scatter(*args, **kwargs)