def transform_algebraic_expression(
        expr: DVar | int | _DynType | Prod | BinConstraintD,
        counter: int,
        dimension_dict: dict[int, int],
    ) -> tuple[_Z3Expr, int]:
        """
        Transforms an algebraic expression to z3 format
        Args:
            expr: An expression is either a dimension variable or an algebraic-expression


        Returns: the transformed expression

        """
        if not (is_algebraic_expression(expr) or is_dim(expr)):
            raise AssertionError("Expected algebraic expression or dimension")

        if is_dim(expr):
            transformed, counter = transform_dimension(
                expr,  # pyrefly: ignore[bad-argument-type]
                counter,
                dimension_dict,
            )
            return transformed.arg(1), counter

        elif isinstance(expr, Prod):
            dims = []
            for dim in expr.products:
                if not is_dim(dim):
                    raise AssertionError("Expected dimension in Prod")
                d, counter = transform_dimension(dim, counter, dimension_dict)
                dims.append(d.arg(1))
            return z3.Product(dims), counter

        elif is_algebraic_expression(expr):
            lhs, counter = transform_algebraic_expression(
                expr.lhs,  # pyrefly: ignore[missing-attribute]
                counter,
                dimension_dict,
            )
            rhs, counter = transform_algebraic_expression(
                expr.rhs,  # pyrefly: ignore[missing-attribute]
                counter,
                dimension_dict,
            )

            if expr.op == op_sub:  # pyrefly: ignore[missing-attribute]
                c = lhs - rhs

            elif expr.op == op_add:
                c = lhs + rhs

            elif expr.op == op_div:
                c = lhs / rhs

            elif expr.op == op_mul:
                c = lhs * rhs

            elif expr.op == op_mod:
                c = lhs % rhs

            else:
                raise NotImplementedError("operation not yet implemented")

            return c, counter

        else:
            raise RuntimeError