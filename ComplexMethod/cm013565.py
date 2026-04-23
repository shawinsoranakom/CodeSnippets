def generate_binconstraint_t(
    constraint: Constraint, counter: int
) -> tuple[Constraint, int]:
    """
    Transform binary constraints for tensors
    """
    if not isinstance(constraint, BinConstraintT):
        raise TypeError(type(constraint))

    # precision constraints
    if constraint.op == op_precision:
        if constraint.lhs == Dyn:
            return T(), counter
        elif isinstance(constraint.lhs, TensorType):
            is_fully_static = all(d != Dyn for d in constraint.lhs.__args__)
            if is_fully_static:
                return BinConstraintT(constraint.lhs, constraint.rhs, op_eq), counter
            else:
                new_dims = []

                for _ in range(len(constraint.lhs.__args__)):
                    dim, counter = gen_dvar(counter)
                    new_dims.append(dim)

                new_dim_constraints = (
                    [
                        BinConstraintD(old_dim, new_dim, op_precision)
                        for new_dim, old_dim in zip(new_dims, constraint.lhs.__args__)
                    ]
                    + [BinConstraintT(constraint.rhs, TensorType(new_dims), op_eq)]
                    + [BinConstraintD(1, new_dim, op_leq) for new_dim in new_dims]
                )
                return Conj(new_dim_constraints), counter
        else:
            return constraint, counter

    # matching
    elif constraint.op == op_matching:
        if not isinstance(constraint.rhs, TensorType):
            raise AssertionError(f"Expected TensorType, got {type(constraint.rhs)}")
        d1 = constraint.rhs.__args__[0]
        d2 = constraint.rhs.__args__[1]
        d3 = constraint.rhs.__args__[2]
        d4 = constraint.rhs.__args__[3]

        conj = [
            BinConstraintT(constraint.lhs, Dyn, op_eq),
            BinConstraintD(d1, Dyn, op_eq),
            BinConstraintD(d2, Dyn, op_eq),
            BinConstraintD(d3, Dyn, op_eq),
            BinConstraintD(d4, Dyn, op_eq),
        ]
        return (
            Disj(
                [
                    Conj(conj),
                    BinConstraintT(constraint.lhs, TensorType([d1, d2, d3, d4]), op_eq),
                ]
            ),
            counter,
        )

    elif constraint.op == op_consistency:
        c_dyn = Disj(
            [
                BinConstraintT(constraint.lhs, Dyn, op_eq),
                BinConstraintT(constraint.rhs, Dyn, op_eq),
            ]
        )
        (
            (
                c_tensor_1,
                c_tensor_2,
                c_tensor_3,
                c_tensor_4,
            ),
            counter,
        ) = gen_consistency_constraints(constraint, counter)

        return Disj([c_dyn, c_tensor_1, c_tensor_2, c_tensor_3, c_tensor_4]), counter

    elif constraint.op == op_leq:
        if not isinstance(constraint.rhs, int):
            raise AssertionError(f"Expected int, got {type(constraint.rhs)}")
        disj = [BinConstraintT(constraint.lhs, Dyn, op_eq)]
        for i in range(1, constraint.rhs + 1):
            dims = []
            for _ in range(1, i + 1):
                dim_var, counter = gen_dvar(counter)
                dims.append(dim_var)
            disj.append(BinConstraintT(constraint.lhs, TensorType(dims), op_eq))
        return Disj(disj), counter
    else:
        return constraint, counter