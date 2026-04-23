def eval_get(
        self,
        expression: expr.GetExpression,
        state: TypeInterpreterState | None = None,
        **kwargs,
    ) -> expr.GetExpression:
        expression = super().eval_get(expression, state=state, **kwargs)
        object_dtype = expression._object._dtype
        index_dtype = expression._index._dtype
        default_dtype = expression._default._dtype

        if object_dtype == dt.JSON:
            # json
            if not dt.dtype_issubclass(default_dtype, dt.Optional(dt.JSON)):
                raise TypeError(
                    f"Default must be of type {Json | None}, found {default_dtype.typehint}."
                )
            if not expression._check_if_exists or default_dtype == dt.JSON:
                return _wrap(expression, dt.JSON)
            else:
                return _wrap(expression, dt.Optional(dt.JSON))
        elif object_dtype.equivalent_to(dt.Optional(dt.JSON)):
            # optional json
            raise TypeError(f"Cannot get from {Json | None}.")
        else:
            # sequence
            if (
                not isinstance(object_dtype, (dt.Array, dt.Tuple, dt.List))
                and object_dtype != dt.ANY
            ):
                raise TypeError(
                    f"Object in {expression!r} has to be a JSON or sequence."
                )
            if index_dtype != dt.INT:
                raise TypeError(f"Index in {expression!r} has to be an int.")

            if isinstance(object_dtype, dt.Array):
                return _wrap(expression, object_dtype.strip_dimension())
            if object_dtype == dt.ANY:
                return _wrap(expression, dt.ANY)

            if isinstance(object_dtype, dt.List):
                if expression._check_if_exists:
                    return _wrap(expression, dt.Optional(object_dtype.wrapped))
                else:
                    return _wrap(expression, object_dtype.wrapped)
            assert isinstance(object_dtype, dt.Tuple)
            if object_dtype == dt.ANY_TUPLE:
                return _wrap(expression, dt.ANY)

            assert not isinstance(object_dtype.args, EllipsisType)
            dtypes = object_dtype.args

            if (
                expression._const_index is None
            ):  # no specified position, index is an Expression
                assert isinstance(dtypes[0], dt.DType)
                return_dtype = dtypes[0]
                for dtype in dtypes[1:]:
                    if isinstance(dtype, dt.DType):
                        return_dtype = dt.types_lca(return_dtype, dtype, raising=False)
                if expression._check_if_exists:
                    return_dtype = dt.types_lca(
                        return_dtype, default_dtype, raising=False
                    )
                return _wrap(expression, return_dtype)

            if not isinstance(expression._const_index, int):
                raise IndexError("Index n")

            try:
                try_ret = dtypes[expression._const_index]
                return _wrap(expression, try_ret)
            except IndexError:
                message = (
                    f"Index {expression._const_index} out of range for a tuple of"
                    + f" type {object_dtype.typehint}."
                )
                if expression._check_if_exists:
                    expression_info = get_expression_info(expression)
                    warnings.warn(
                        message
                        + " It refers to the following expression:\n"
                        + expression_info
                        + "Consider using just the default value without .get()."
                    )
                    return _wrap(expression, default_dtype)
                else:
                    raise IndexError(message)