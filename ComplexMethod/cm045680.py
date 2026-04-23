def _eval_binary_op_on_tuples(
        self,
        left_dtype: dt.DType,
        right_dtype: dt.DType,
        operator: Any,
        expression: expr.ColumnExpression,
    ) -> dt.DType | None:
        if (
            isinstance(left_dtype, (dt.Tuple, dt.List))
            and isinstance(right_dtype, (dt.Tuple, dt.List))
            and operator in tuple_handling_operators
        ):
            if left_dtype == dt.ANY_TUPLE or right_dtype == dt.ANY_TUPLE:
                return dt.BOOL
            left_args, right_args = dt.broadcast_tuples(left_dtype, right_dtype)
            if (
                isinstance(left_args, tuple)
                and isinstance(right_args, tuple)
                and len(left_args) == len(right_args)
            ):
                results = []
                is_valid = True
                for left_arg, right_arg in zip(left_args, right_args):
                    if not isinstance(left_arg, EllipsisType) and not isinstance(
                        right_arg, EllipsisType
                    ):
                        try:
                            results.append(
                                self._eval_binary_op(
                                    left_arg, right_arg, operator, expression
                                )
                            )
                        except TypeError:
                            is_valid = False
                            break
                if is_valid:
                    assert all(result == results[0] for result in results)
                    return dt.wrap(results[0])
        return None