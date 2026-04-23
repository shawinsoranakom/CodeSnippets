def constant(value, dtype):
        if isinstance(value, ValueRanges):
            if not value.is_singleton():
                raise AssertionError("ValueRanges must be a singleton for constant()")
            value = value.lower
        # NB: value is NOT a sympy expression, it's a constant!
        is_python = isinstance(value, (int, float, bool))
        if not is_python and not isinstance(
            value, (BooleanAtom, sympy.Integer, sympy.Number)
        ):
            raise AssertionError(f"not a supported constant type: {type(value)}")

        # using nan makes subsequent computation throw, and for the purposes of optimization
        # returning -math.inf - math.inf is equivalent to giving up
        if isinstance(value, SupportsFloat) and math.isnan(value):
            if dtype == torch.bool:
                return ValueRanges.unknown_bool()
            elif dtype.is_floating_point:
                return ValueRanges.unknown()
            else:
                return ValueRanges.unknown_int()

        if is_python:
            type_ = dtype_to_type(dtype)
            value = type_(value)
        else:
            # We do a type check on a best-effort basis
            # We don't want to force a cast to sympy.Float if the value is Rational to avoid losing precision
            if dtype == torch.bool:
                if not isinstance(value, BooleanAtom):
                    raise AssertionError("expected BooleanAtom for bool dtype")
            elif dtype.is_floating_point:
                # pyrefly: ignore [missing-attribute]
                if value.is_finite and not value.is_real:
                    raise AssertionError(
                        "expected float-like sympy value for float dtype"
                    )
            else:
                # dtype is intXX
                if not getattr(value, "is_integer", False):
                    raise AssertionError("expected integer sympy value for int dtype")

        r = ValueRanges.wrap(value)
        return r