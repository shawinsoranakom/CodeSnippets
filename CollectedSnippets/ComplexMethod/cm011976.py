def default_accumulator(
        reduction_type: str, dtype: torch.dtype
    ) -> _NumLike | Sequence[_NumLike]:
        if reduction_type in ("max", "argmax"):
            if is_float_dtype(dtype):
                return float("-inf")
            elif is_boolean_dtype(dtype):
                return False
            else:
                return torch.iinfo(dtype).min
        if reduction_type in ("min", "argmin"):
            if is_float_dtype(dtype):
                return float("inf")
            elif is_boolean_dtype(dtype):
                return True
            else:
                return torch.iinfo(dtype).max

        zero = False if is_boolean_dtype(dtype) else 0
        one = True if is_boolean_dtype(dtype) else 1
        return {
            "sum": zero,
            "prod": one,
            "dot": zero,
            "xor_sum": zero,
            "any": zero,
            "welford_reduce": (zero, zero, zero),
            "welford_combine": (zero, zero, zero),
            "online_softmax_reduce": (float("-inf"), zero),
        }[reduction_type]