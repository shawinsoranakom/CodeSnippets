def _get_existing_inline_assertions(
    graph_module: torch.fx.GraphModule,
    range_constraints: dict[sympy.Symbol, ValueRanges],
) -> dict[sympy.Symbol, ValueRanges]:
    existing_inline_assertions: dict[sympy.Symbol, ValueRanges] = {}

    for module in graph_module.modules():
        if not isinstance(module, torch.fx.GraphModule):
            continue

        # Find all the existing inline assertions. They will look something like:
        # %_local_scalar_dense = call_function[target=torch.ops.aten._local_scalar_dense.default](args = (%arg1_1,), kwargs = {})
        # %ge = call_function[target=operator.ge](args = (%_local_scalar_dense, 0), kwargs = {})
        # %_assert_scalar = call_function[target=torch.ops.aten._assert_scalar.default](args = (%scalar_tensor, "..."), kwargs = {})
        for node in module.graph.nodes:
            if node.target != torch.ops.aten._assert_scalar.default:
                continue

            compare_arg = node.args[0]
            if not (
                isinstance(compare_arg, torch.fx.Node)
                and compare_arg.op == "call_function"
                and compare_arg.target in (operator.le, operator.ge)
                and len(compare_arg.args) == 2
            ):
                continue

            compare_op = compare_arg.target
            lhs, rhs = compare_arg.args

            def maybe_get_symint(x):
                if (
                    isinstance(x, torch.fx.Node)
                    and "val" in x.meta
                    and isinstance(x.meta["val"], torch.SymInt)
                ):
                    return x.meta["val"].node.expr
                return x

            lhs = maybe_get_symint(lhs)
            rhs = maybe_get_symint(rhs)

            if compare_op is operator.ge:
                lhs, rhs = rhs, lhs

            if isinstance(lhs, sympy.Symbol) and isinstance(rhs, int):
                symint = lhs
                scalar = rhs
            elif isinstance(rhs, sympy.Symbol) and isinstance(lhs, int):
                symint = rhs
                scalar = lhs
            else:
                continue

            if symint not in range_constraints:
                raise RuntimeError(
                    f"Unable to find symint {symint} in {range_constraints}"
                )

            previous_range = existing_inline_assertions.get(
                symint, ValueRanges(-math.inf, math.inf)
            )

            if symint is lhs:
                bounds = ValueRanges(-math.inf, scalar)
            else:
                bounds = ValueRanges(scalar, math.inf)
            existing_inline_assertions[symint] = previous_range & bounds

    return existing_inline_assertions