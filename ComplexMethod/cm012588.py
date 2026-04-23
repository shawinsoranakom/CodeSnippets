def pow(cls, a, b):
        result_dtype = get_dtype_handler().pow(a, b)
        if result_dtype is not None and is_integer_dtype(result_dtype):
            base = cls._cast_libdevice_arg(a, result_dtype)
            exponent = (
                cls.constant(b, torch.int64)
                if isinstance(b, torch._prims_common.Number)
                else f"{b}"
            )
            return f"triton_helpers.pow_integer({base}, {exponent})"

        any_needs_upcast = needs_upcast_to_float32(a) or needs_upcast_to_float32(b)
        pow_dtype = result_dtype
        if pow_dtype not in (torch.float32, torch.float64):
            # libdevice.pow only accepts fp32/fp64. Keep low-precision floating
            # cases on the existing fp32 path, and otherwise fall back to fp64
            # for symbolic integer scalar pow expressions like 2 ** ks0.
            pow_dtype = (
                torch.float32
                if low_precision_fp(result_dtype) or any_needs_upcast
                else torch.float64
            )

        cast_a = cls._cast_libdevice_arg(a, pow_dtype)
        cast_b = cls._cast_libdevice_arg(b, pow_dtype)
        result = f"libdevice.pow({cast_a}, {cast_b})"
        if result_dtype is not None and result_dtype != pow_dtype:
            if low_precision_fp(result_dtype):
                if any_needs_upcast:
                    result = f"{result}.to({triton_type(result_dtype)})"
            else:
                result = f"{result}.to({triton_type(result_dtype)})"
        return result