def getitem_inference_rule(
    n: Node, symbols: _SymbolDict, constraints: list[Constraint], counter: int
) -> tuple[list[Constraint], int]:
    if not isinstance(n.args[0], Node):
        raise AssertionError(f"Expected Node, got {type(n.args[0])}")

    # dimension output case
    if isinstance(n.args[1], int):
        # create and store the new dimension variable
        get_item_output, counter = gen_dvar(counter)
        symbols[n] = get_item_output

        # retrieve arg variables
        get_item_arg = symbols[n.args[0]]
        if not isinstance(get_item_arg, TVar):
            raise AssertionError(f"Expected TVar, got {type(get_item_arg)}")

        # if the input is dynamic, we accept any index and return
        # a dynamic dimension as output
        input_dyn = BinConstraintT(get_item_arg, Dyn, op_eq)
        output_dyn = BinConstraintD(get_item_output, Dyn, op_eq)
        c1 = Conj([input_dyn, output_dyn])

        # if the input is a tensor,
        # generate a getItem constraint which will be expanded based on the
        # tensor dimension.

        c2 = [
            GetItem(i + 1, n.args[1], get_item_output, get_item_arg)
            for i in range(MAX_TENSOR_RANK)
        ]

        # since the output is a dimension, we make sure it's a natural number
        # added as a conjunction to the disjunction of c2
        c3 = BinConstraintD(0, get_item_output, op_leq)
        return [Disj([c1, Conj([Disj(c2), c3])])], counter

    # tensor output case
    elif isinstance(n.args[1], tuple):
        # create and store the new tensor variable
        get_item_output, counter = gen_tvar(counter)  # type: ignore[arg-type,assignment]
        symbols[n] = get_item_output

        # retrieve arg variables
        if n.args[0] in symbols:
            get_item_arg = symbols[n.args[0]]
            if not isinstance(get_item_arg, TVar):
                raise AssertionError(f"Expected TVar, got {type(get_item_arg)}")

            input_dyn = BinConstraintT(get_item_arg, Dyn, op_eq)
            output_dyn = BinConstraintT(get_item_output, Dyn, op_eq)  # type: ignore[assignment]
            c1 = Conj([input_dyn, output_dyn])

            c2 = [
                GetItemTensor(i + 1, n.args[1], get_item_output, get_item_arg)  # type: ignore[misc]
                for i in range(MAX_TENSOR_RANK)
            ]
        else:
            # TODO: we should figure out why there is a key-error here.
            return [], counter  # pyrefly: ignore[implicit-any]

        return [Disj([c1, *c2])], counter

    else:
        raise RuntimeError("Method not yet implemented")