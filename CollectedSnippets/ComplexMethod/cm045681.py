def eval_pointer(
        self,
        expression: expr.PointerExpression,
        state: TypeInterpreterState | None = None,
        **kwargs,
    ) -> expr.PointerExpression:
        expression = super().eval_pointer(expression, state=state, **kwargs)
        arg_types = [arg._dtype for arg in expression._args]
        if expression._instance is not None:
            arg_types.append(expression._instance._dtype)
        self._check_for_disallowed_types("pathway.pointer_from", *arg_types)
        if expression._optional and any(
            isinstance(arg, dt.Optional) or arg == dt.ANY for arg in arg_types
        ):
            return _wrap(
                expression,
                dt.Optional(dt.Pointer(*[dt.unoptionalize(arg) for arg in arg_types])),
            )
        else:
            return _wrap(expression, dt.Pointer(*arg_types))