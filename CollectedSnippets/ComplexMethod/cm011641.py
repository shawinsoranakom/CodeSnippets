def to_dtype(
        x: Any,
        dtype: torch.dtype,
        src_dtype: torch.dtype | None = None,
        use_compute_types: bool = True,
    ) -> ValueRanges[Any]:
        x = ValueRanges.wrap(x)

        if dtype == torch.bool:
            if x.is_singleton():
                return ValueRanges.wrap(x.lower != 0)
            elif x.is_bool:
                return x
            elif 0 not in x:
                return ValueRanges.wrap(sympy.true)
            else:
                return ValueRanges(sympy.false, sympy.true)

        def cast(x: Any, dtype: torch.dtype) -> sympy.Expr:
            # dtype is int or float
            if dtype.is_floating_point:
                return sympy.Float(x)
            else:
                if x in (int_oo, -int_oo):
                    return x
                try:
                    return sympy.Integer(x)
                except TypeError:
                    # inf cannot be cast to Integer
                    return x

        if x.is_bool:
            if x.is_singleton():
                val = 1 if x.lower else 0
                return ValueRanges.wrap(cast(val, dtype))
            else:
                return ValueRanges(cast(0, dtype), cast(1, dtype))
        else:
            # int to float or float to int
            return ValueRanges(cast(x.lower, dtype), cast(x.upper, dtype))