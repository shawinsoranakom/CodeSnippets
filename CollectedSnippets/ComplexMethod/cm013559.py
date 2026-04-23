def transform_to_z3(
        constraint: Constraint, counter: int, dimension_dict: dict[int, int]
    ) -> tuple[_Z3Expr, int]:
        if isinstance(constraint, Conj):
            conjuncts = []
            for c in constraint.conjucts:
                new_c, counter = transform_to_z3(c, counter, dimension_dict)
                conjuncts.append(new_c)
            return z3.And(conjuncts), counter

        elif isinstance(constraint, Disj):
            disjuncts = []
            for c in constraint.disjuncts:
                new_c, counter = transform_to_z3(c, counter, dimension_dict)
                disjuncts.append(new_c)
            return z3.Or(disjuncts), counter

        elif isinstance(constraint, T):
            return True, counter

        elif isinstance(constraint, F):
            return False, counter

        elif isinstance(constraint, BinConstraintT):
            if constraint.op == op_eq:
                lhs, counter = transform_var(
                    constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                rhs, counter = transform_var(
                    constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                return (lhs == rhs), counter

            else:
                raise NotImplementedError("Method not yet implemented")

        elif isinstance(constraint, BinConstraintD):
            if constraint.op == op_eq:
                if isinstance(constraint.lhs, BVar) and is_bool_expr(constraint.rhs):
                    transformed_rhs, counter = transform_to_z3(
                        constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                        counter,
                        dimension_dict,
                    )
                    transformed_lhs = z3.Bool(constraint.lhs.c)
                    return transformed_lhs == transformed_rhs, counter

                elif is_dim(constraint.lhs) and is_dim(constraint.rhs):
                    # with dimension transformations we consider the encoding
                    lhs, counter = transform_dimension(
                        constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                        counter,
                        dimension_dict,
                    )
                    rhs, counter = transform_dimension(
                        constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                        counter,
                        dimension_dict,
                    )
                    return lhs == rhs, counter

                else:
                    # then we have an algebraic expression which means that we disregard the
                    # first element of the encoding
                    lhs, counter = transform_algebraic_expression(
                        constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                        counter,
                        dimension_dict,
                    )
                    rhs, counter = transform_algebraic_expression(
                        constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                        counter,
                        dimension_dict,
                    )
                    return lhs == rhs, counter

            # The assumption here is that the LHS and RHS must be dimensions
            elif constraint.op == op_neq:
                if not is_dim(constraint.lhs):
                    raise AssertionError("Expected lhs to be a dimension")
                if not is_dim(constraint.rhs):
                    raise AssertionError("Expected rhs to be a dimension")
                lhs, counter = transform_dimension(
                    constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                rhs, counter = transform_dimension(
                    constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                if constraint.rhs == Dyn or constraint.lhs == Dyn:
                    if constraint.rhs == Dyn:
                        return lhs.arg(0) == 1, counter
                    else:
                        return rhs.arg(0) == 1, counter

                # if one of the instances is a number
                elif isinstance(constraint.lhs, int) or isinstance(constraint.rhs, int):
                    if isinstance(constraint.lhs, int):
                        return (
                            z3.Or(
                                [
                                    rhs.arg(0) == 0,
                                    z3.And([rhs.arg(0) == 1, lhs.arg(1) != rhs.arg(1)]),
                                ]
                            ),
                            counter,
                        )

                    else:
                        return (
                            z3.Or(
                                [
                                    lhs.arg(0) == 0,
                                    z3.And([lhs.arg(0) == 1, lhs.arg(1) != rhs.arg(1)]),
                                ]
                            ),
                            counter,
                        )

                else:
                    return (
                        z3.Or(
                            [
                                z3.And([lhs.arg(0) == 0, rhs.arg(0) != 0]),
                                z3.And([lhs.arg(0) != 0, rhs.arg(0) == 0]),
                                z3.And(
                                    [
                                        lhs.arg(0) != 0,
                                        rhs.arg(0) != 0,
                                        lhs.arg(1) != rhs.arg(1),
                                    ]
                                ),
                            ]
                        ),
                        counter,
                    )

            elif constraint.op == op_leq:
                # if the dimensions are not dyn, this will come into effect
                # there would have been another constraint specifying if a given dimension
                # is dyn or not
                if not (is_dim(constraint.lhs) and is_dim(constraint.rhs)):
                    raise AssertionError("Expected both lhs and rhs to be dimensions")
                lhs, counter = transform_algebraic_expression(
                    constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                rhs, counter = transform_algebraic_expression(
                    constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                return lhs <= rhs, counter

            elif constraint.op == op_gt:
                if not (is_dim(constraint.lhs) and is_dim(constraint.rhs)):
                    raise AssertionError("Expected both lhs and rhs to be dimensions")
                lhs, counter = transform_algebraic_expression(
                    constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                rhs, counter = transform_algebraic_expression(
                    constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                return lhs > rhs, counter

            elif constraint.op == op_lt:
                if not (is_dim(constraint.lhs) and is_dim(constraint.rhs)):
                    raise AssertionError("Expected both lhs and rhs to be dimensions")
                lhs, counter = transform_algebraic_expression(
                    constraint.lhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                rhs, counter = transform_algebraic_expression(
                    constraint.rhs,  # pyrefly: ignore[bad-argument-type]
                    counter,
                    dimension_dict,
                )
                return lhs < rhs, counter

            else:
                raise NotImplementedError("operation not yet implemented")

        else:
            raise NotImplementedError("Operation not yet implemented")