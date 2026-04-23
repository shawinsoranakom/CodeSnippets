def expand_inference_rule(
    n: Node, symbols: _SymbolDict, constraints: list[Constraint], counter: int
) -> tuple[list[Constraint], int]:
    """
    We generate the exact constraints as we do for tensor additions but we constraint
    the rank of this expression to be equal to len(n.args[1:]) so that only
    those cases get considered for the output
    """
    if not isinstance(n.args[0], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[0])}")

    # define the output for expand
    expand, counter = gen_tvar(counter)
    symbols[n] = expand

    # since we do not have two nodes here, we will construct an argument variable
    e1 = symbols[n.args[0]]
    e2, counter = gen_tvar(counter)

    e2_nat_constraints = []
    for arg in n.args[1:]:
        if not isinstance(arg, (Node, int)):
            raise AssertionError(f"Expected Node or int, got {type(arg)}")
        if isinstance(arg, Node):
            if not isinstance(symbols[arg], DVar):
                raise AssertionError(f"Expected DVar, got {type(symbols[arg])}")
            e2_nat_constraints.append(BinConstraintD(0, symbols[arg], op_leq))

    e2_constraint = BinConstraintT(
        e2,
        TensorType(
            [
                arg
                if isinstance(arg, int)
                else symbols[arg]  # pyrefly: ignore[bad-index]
                for arg in n.args[1:]
            ]
        ),
        op_eq,
    )

    constraints, counter = gen_broadcasting_constraints(
        e1,  # pyrefly: ignore[bad-argument-type]
        e2,
        symbols,
        counter,
        expand,
    )

    # constraint the output size
    dims, counter = gen_tensor_dims(len(n.args[1:]), counter)
    nat_constraints = gen_nat_constraints(dims)
    c = [
        BinConstraintT(expand, TensorType(dims), op_eq),
        *nat_constraints,
        e2_constraint,
        *e2_nat_constraints,
    ]
    constraints += c

    return constraints, counter