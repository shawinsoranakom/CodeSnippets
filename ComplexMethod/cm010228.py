def deserialize_shape(
        val: None | int | str,
    ) -> None | int | Dim | _DimHint:
        if val is None or isinstance(val, int):
            return val
        elif val == "_DimHint.AUTO":
            return _DimHint.AUTO()
        elif val == "_DimHint.DYNAMIC":
            return _DimHint.DYNAMIC()
        elif val == "_DimHint.STATIC":
            return _DimHint.STATIC()
        if not isinstance(val, str):
            raise UserError(
                UserErrorType.INVALID_INPUT,
                "Expected leaves in `spec['dynamic_shapes']` to be ints, None, Dim.AUTO/STATIC, symbols, "
                f" or derived expressions, got {val}",
            )
        if val not in dim_cache:
            raise UserError(
                UserErrorType.INVALID_INPUT,
                "Expected dims in `spec['dynamic_shapes']` to be tracked in `spec['dims']`, "
                f"got {val} which is not in {dims.keys()}",
            )
        return dim_cache[val]