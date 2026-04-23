def _wrap(left_tab: table.Joinable, context: ContextType):
        right_tab, context = _run(node.args.pop("this"), context)
        assert isinstance(right_tab, table.Joinable)
        if (on_field := node.args.pop("on", None)) is not None:

            def _rec(
                op: sql_expr.And | sql_expr.EQ,
            ) -> list[expr.ColumnBinaryOpExpression]:
                if isinstance(op, sql_expr.And):
                    return _rec(op.this) + _rec(op.expression)
                else:
                    return [_run(op, context)]

            on_all = _rec(on_field)

            def _test(e: expr.ColumnExpression) -> bool:
                if not isinstance(e, expr.ColumnBinaryOpExpression):
                    return False
                if e._operator != operator.eq:
                    return False
                left_side = e._left
                if not isinstance(left_side, expr.ColumnReference):
                    return False
                right_side = e._right
                if not isinstance(right_side, expr.ColumnReference):
                    return False
                return (
                    left_side.table in left_tab._subtables()
                    and right_side.table in right_tab._subtables()
                )

            on = []
            postfilter = []
            for e in on_all:
                if _test(e):
                    on.append(e)
                else:
                    postfilter.append(e)

        elif using_field := node.args.pop("using", None):
            on = []
            for arg in using_field:
                name = _identifier(arg)
            on.append(thisclass.left[name] == thisclass.right[name])
            postfilter = []
        else:
            on = []
            postfilter = []

        node.args.pop("kind", None)
        side = node.args.pop("side", "")
        _check_work_done(node)

        if side == "OUTER":
            # TODO we should properly handle those cases
            assert (
                len(postfilter) == 0
            ), "Not supported ON clause for OUTER JOIN, if possible use WHERE"
            return left_tab.join_outer(right_tab, *on), context
        elif side == "LEFT":
            assert (
                len(postfilter) == 0
            ), "Not supported ON clause for LEFT JOIN, if possible use WHERE"
            return left_tab.join_left(right_tab, *on), context
        elif side == "RIGHT":
            assert (
                len(postfilter) == 0
            ), "Not supported ON clause for RIGHT JOIN, if possible use WHERE"
            return left_tab.join_left(right_tab, *on), context
        else:
            assert side in ["INNER", ""]
            ret = left_tab.join(right_tab, *on)
            for fil in postfilter:
                ret = ret.filter(fil)
            return ret, context