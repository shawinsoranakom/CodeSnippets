def generate_calc_product(
    constraint: Constraint, counter: int
) -> tuple[Constraint, int]:
    """
    Transform flatten constraints
    """
    if not isinstance(constraint, CalcProduct):
        raise TypeError(type(constraint))
    start = constraint.start
    end = constraint.end
    dims = constraint.dims_to_flatten
    flattened = constraint.flattened
    n = len(constraint.dims_to_flatten)

    # this will be evaluated right here
    boundary_check = 0 <= start and start < end and end <= n

    c_boundary = T() if boundary_check else F()

    lhs = dims[0:start]
    rhs = dims[end:]
    mid = dims[start:end]

    all_possibilities = generate_all_int_dyn_dim_possibilities(mid)

    all_constraints: list[Constraint] = []

    for p in all_possibilities:
        p = list(p)
        # this tells us there is a dynamic variable
        contains_dyn = not all(constraint.op == op_neq for constraint in p)
        if contains_dyn:
            mid_var = [Dyn]
            total_constraints = lhs + mid_var + rhs
            if len(total_constraints) > 4:
                all_constraints.append(F())
            else:
                all_constraints.append(
                    Conj(
                        [
                            BinConstraintT(
                                flattened, TensorType(lhs + mid_var + rhs), op_eq
                            )
                        ]
                        + p
                    )
                )
        else:
            new_var, counter = gen_dvar(counter)
            mid_eq_prod = Conj(
                [
                    BinConstraintD(new_var, Prod(mid), op_eq),
                    BinConstraintD(new_var, Dyn, op_neq),
                ]
            )
            mid_var = [new_var]
            total_constraints = lhs + mid_var + rhs
            if len(total_constraints) > 4:
                all_constraints.append(F())
            else:
                all_constraints.append(
                    Conj(
                        [
                            BinConstraintT(
                                flattened, TensorType(lhs + mid_var + rhs), op_eq
                            ),
                            mid_eq_prod,
                        ]
                        + p
                    )
                )

    return Conj([Disj(all_constraints), c_boundary]), counter