def eval_ifelse(
        self,
        expression: expr.IfElseExpression,
        state: TypeInterpreterState | None = None,
        **kwargs,
    ) -> expr.IfElseExpression:
        assert state is not None
        if_ = self.eval_expression(expression._if, state=state, **kwargs)
        if_dtype = if_._dtype
        if if_dtype != dt.BOOL:
            raise TypeError(
                f"First argument of pathway.if_else has to be bool, found {if_dtype.typehint}."
            )

        if isinstance(if_, expr.IsNotNoneExpression) and isinstance(
            if_._expr, expr.ColumnReference
        ):
            then_ = self.eval_expression(
                expression._then, state=state.with_new_col([if_._expr]), **kwargs
            )
        else:
            then_ = self.eval_expression(expression._then, state=state, **kwargs)

        if isinstance(if_, expr.IsNoneExpression) and isinstance(
            if_._expr, expr.ColumnReference
        ):
            else_ = self.eval_expression(
                expression._else, state=state.with_new_col([if_._expr], **kwargs)
            )
        else:
            else_ = self.eval_expression(expression._else, state=state, **kwargs)

        then_dtype = then_._dtype
        else_dtype = else_._dtype
        try:
            lca = dt.types_lca(then_dtype, else_dtype, raising=True)
        except TypeError:
            raise TypeError(
                f"Cannot perform pathway.if_else on columns of types {then_dtype.typehint} and {else_dtype.typehint}."
            )
        if lca is dt.ANY:
            raise TypeError(
                f"Cannot perform pathway.if_else on columns of types {then_dtype.typehint} and {else_dtype.typehint}."
            )
        expression = expr.IfElseExpression(if_, then_, else_)
        return _wrap(expression, lca)