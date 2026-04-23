def broadcasting_inference_rule(
    n: Node, symbols: _SymbolDict, constraints: list[Constraint], counter: int
) -> tuple[list[Constraint], int]:  # pyrefly: ignore[bad-return]
    op_code = None
    if n.target is operator.add or n.target is torch.add:
        op_code = op_add
    elif n.target is operator.mul:
        op_code = op_mul

    if isinstance(n.args[0], Node) and isinstance(n.args[1], Node):
        if isinstance(symbols[n.args[0]], TVar) and isinstance(
            symbols[n.args[1]], TVar
        ):
            my_output, counter = gen_tvar(counter)
            symbols[n] = my_output
            e1 = symbols[n.args[0]]
            e2 = symbols[n.args[1]]

            return gen_broadcasting_constraints(
                e1,  # pyrefly: ignore[bad-argument-type]
                e2,  # pyrefly: ignore[bad-argument-type]
                symbols,
                counter,
                my_output,
            )
        else:
            raise NotImplementedError("Method not yet implemented")

    elif isinstance(n.args[0], Node) and isinstance(n.args[1], (int, float)):
        if isinstance(symbols[n.args[0]], TVar):
            my_output, counter = gen_tvar(counter)
            symbols[n] = my_output
            e1 = symbols[n.args[0]]
            return [BinConstraintT(my_output, e1, op_eq)], counter
        elif isinstance(symbols[n.args[0]], DVar):
            my_output, counter = gen_dvar(counter)  # type: ignore[arg-type,assignment]
            symbols[n] = my_output
            e1 = symbols[n.args[0]]

            # we will propagate the runtime value here since this is regular addition
            c = Conj(
                [
                    BinConstraintD(
                        my_output, BinConstraintD(e1, n.args[1], op_code), op_eq
                    ),
                    BinConstraintD(0, my_output, op_leq),
                ]
            )
            return [c], counter

    elif isinstance(n.args[1], Node) and isinstance(n.args[0], (int, float)):
        if isinstance(symbols[n.args[1]], TVar):
            my_output, counter = gen_tvar(counter)
            symbols[n] = my_output
            e2 = symbols[n.args[1]]
            return [BinConstraintT(my_output, e2, op_eq)], counter
        elif isinstance(symbols[n.args[1]], DVar):
            my_output, counter = gen_dvar(counter)  # type: ignore[arg-type,assignment]
            symbols[n] = my_output
            e2 = symbols[n.args[1]]

            # we will propagate the runtime value here since this is regular addition
            c = Conj(
                [
                    BinConstraintD(
                        my_output, BinConstraintD(e2, n.args[0], op_code), op_eq
                    ),
                    BinConstraintD(0, my_output, op_leq),
                ]
            )
            return [c], counter

        else:
            raise NotImplementedError("Method not yet implemented")

    else:
        # TODO generate add constraints for scalar addition
        raise NotImplementedError("Addition not yet implemented")