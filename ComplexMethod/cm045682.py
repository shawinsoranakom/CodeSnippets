def eval_coalesce(
        self,
        expression: expr.CoalesceExpression,
        state: TypeInterpreterState | None = None,
        **kwargs,
    ) -> expr.CoalesceExpression:
        expression = super().eval_coalesce(expression, state=state, **kwargs)
        dtypes = [arg._dtype for arg in expression._args]
        self._check_for_disallowed_types("pathway.coalesce", *dtypes)
        ret_type = dtypes[0]
        non_optional_arg = False
        for dtype in dtypes:
            try:
                ret_type = dt.types_lca(dtype, ret_type, raising=True)
            except TypeError:
                raise TypeError(
                    "Incompatible types in for a coalesce expression.\n"
                    + f"The types are: {dtypes}. "
                    + "You might try casting the expressions to Any type to circumvent this, "
                    + "but this is most probably an error."
                )
            if not isinstance(dtype, dt.Optional):
                # FIXME: do we want to be more radical and return now?
                # Maybe with a warning that some args are skipped?
                non_optional_arg = True
        if ret_type is dt.ANY and any(dtype is not dt.ANY for dtype in dtypes):
            raise TypeError(
                f"Cannot perform pathway.coalesce on columns of types {[dtype.typehint for dtype in dtypes]}."
            )
        ret_type = dt.unoptionalize(ret_type) if non_optional_arg else ret_type
        return _wrap(expression, ret_type)