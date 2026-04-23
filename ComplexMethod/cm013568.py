def equality_inference_rule(
    n: Node, symbols: _SymbolDict, constraints: list[Constraint], counter: int
) -> tuple[list[Constraint], int]:
    """
    We generate the constraint: input = output
    """
    output, counter = gen_tvar(counter)
    symbols[n] = output

    if isinstance(n.args[0], Node):
        input = symbols[n.args[0]]
        if isinstance(input, TVar):
            return [BinConstraintT(input, output, op_eq)], counter

        # then we have dimension variables
        else:
            for arg in n.args:
                if not isinstance(symbols[arg], DVar):  # pyrefly: ignore[bad-index]
                    raise AssertionError(
                        f"Expected DVar, got {type(symbols[arg])}"  # pyrefly: ignore[bad-index]
                    )
        my_size = [symbols[arg] for arg in n.args]  # pyrefly: ignore[bad-index]
        return [BinConstraintT(output, TensorType(my_size), op_eq)], counter

    elif isinstance(n.args[0], tuple):
        # then the tuple is the size
        if len(n.args[0]) > 4:
            raise AssertionError(f"Expected len <= 4, got {len(n.args[0])}")
        my_size = [symbols[arg] for arg in n.args[0]]  # pyrefly: ignore[bad-index]
        return [BinConstraintT(output, TensorType(my_size), op_eq)], counter
    else:
        raise NotImplementedError("Method not yet implemented")