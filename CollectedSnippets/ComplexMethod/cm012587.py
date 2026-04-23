def tanh(x):
        cse_var = V.kernel.cse.varname_map.get(x)
        if cse_var and hasattr(cse_var, "dtype"):
            dtype = cse_var.dtype
        else:
            dtype = None
        if (
            config.use_fast_math
            and torch.version.hip
            and get_triton_version() > (3, 5)
            and dtype != torch.float64
            and dtype is not None
        ):
            # Requires upstream Triton 3.6+ for latest fast_tanhf support
            # https://github.com/triton-lang/triton/pull/8551
            return f"libdevice.fast_tanhf({x})"
        else:
            return f"libdevice.tanh({x})"