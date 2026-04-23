def lt_inference_rule(
    n: Node, symbols: _SymbolDict, constraints: list[Constraint], counter: int
) -> tuple[list[Constraint], int]:
    if not isinstance(n.args[0], (Node, int)):
        raise AssertionError(f"Expected Node or int, got {type(n.args[0])}")
    if not isinstance(n.args[1], (Node, int)):
        raise AssertionError(f"Expected Node or int, got {type(n.args[1])}")

    # We make sure this node will not be used again. We do not
    # generate a constraint about that node. Only about the operands.

    e1 = symbols[n.args[0]] if isinstance(n.args[0], Node) else n.args[0]
    e2 = symbols[n.args[1]] if isinstance(n.args[1], Node) else n.args[1]

    if isinstance(n.args[0], Node) and isinstance(n.args[1], Node):
        if isinstance(e1, TVar) and isinstance(e2, TVar):
            lt_tensor, counter = gen_tvar(counter)
            symbols[n] = lt_tensor
            return gen_broadcasting_constraints(e1, e2, symbols, counter, lt_tensor)

        elif isinstance(e1, DVar) and isinstance(e2, DVar):
            # This is meant to be used for flow analysis only
            lt_constraint = BinConstraintD(e1, e2, op_lt)

            my_lt, counter = gen_bvar(counter)
            equality_constraint = BinConstraintD(my_lt, lt_constraint, op_eq)
            return [equality_constraint], counter

        else:
            raise RuntimeError("Sort Mismatch")

    elif isinstance(n.args[0], Node) and not isinstance(n.args[1], Node):
        if isinstance(e1, DVar):
            # This is meant to be used for flow analysis only
            lt_constraint = BinConstraintD(e1, e2, op_lt)

            my_lt, counter = gen_bvar(counter)
            equality_constraint = BinConstraintD(my_lt, lt_constraint, op_eq)
            return [equality_constraint], counter
        else:
            raise NotImplementedError("Method not yet implemented")

    else:
        raise NotImplementedError("Method not yet implemented")