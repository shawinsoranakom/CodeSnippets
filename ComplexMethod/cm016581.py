def post_cast(s, param_key, x, dtype, resident, update_weight):
        lowvram_fn = getattr(s, param_key + "_lowvram_function", None)
        fns = getattr(s, param_key + "_function", [])

        orig = x

        def to_dequant(tensor, dtype):
            tensor = tensor.to(dtype=dtype)
            if isinstance(tensor, QuantizedTensor):
                tensor = tensor.dequantize()
            return tensor

        if orig.dtype != dtype or len(fns) > 0:
            x = to_dequant(x, dtype)
        if not resident and lowvram_fn is not None:
            x = to_dequant(x, dtype if compute_dtype is None else compute_dtype)
            x = lowvram_fn(x)
            if (want_requant and len(fns) == 0 or update_weight):
                seed = comfy.utils.string_to_seed(s.seed_key)
                if isinstance(orig, QuantizedTensor):
                    y = QuantizedTensor.from_float(x, s.layout_type, scale="recalculate", stochastic_rounding=seed)
                else:
                    y = comfy.float.stochastic_rounding(x, orig.dtype, seed=seed)
            if want_requant and len(fns) == 0:
                x = y
            if update_weight:
                orig.copy_(y)
        for f in fns:
            x = f(x)
        return x