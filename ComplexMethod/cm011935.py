def try_to_reduce_precision(
    node: Any,
    bounds: dict[Any, Any],
    indirect_vars: list[Any],
    indices: dict[Any, sympy.Expr],
    replacement_vals: dict[Any, ValueRanges[sympy.Expr]],
) -> None:
    # if a downstream use of a node explicitly converts to int32, or float16/float32/float64,
    # then it's precision is set for that chain of uses, and we don't need to consider those
    # dominated values
    def skip_filter(node: Any) -> bool:
        return node.target == "to_dtype" and node.args[2] in (
            torch.int32,
            torch.float32,
            torch.float64,
        )

    # TODO - there are dominated uses whose dtype does not depend on whether
    # we reduce the precision here, e.g. add(int64, int64) one of the args can be reduced to
    # int32 without changing the output precision of the node. this case hasn't shown up
    for dominated in dominated_nodes([node], skip_filter):
        if dominated.target in ["store", "output"]:
            continue

        if isinstance(dominated.target, str) and "set_indirect" in dominated.target:
            idx = int(dominated.target[len("set_indirect") :])
            indirect_var = indirect_vars[idx]

            # We check that we can compute all the indices it's involved in with int32
            for index, expr in indices.items():
                if indirect_var in expr.free_symbols:
                    index_val = replacement_vals[index]

                    if math.isinf(index_val.lower) or math.isinf(index_val.upper):
                        return

                    # all indices are integers, so make sure that we
                    # use the bounds of integers instead of floats.
                    # TODO - not sure if we should be doing int/float casts while tracing,
                    # might interfere with sympy.

                    index_val_int = ValueRanges[sympy.Expr](
                        int(index_val.lower), int(index_val.upper)
                    )
                    if not range_expressable_in_32_bits(index_val_int):
                        return

        if not range_expressable_in_32_bits(bounds[dominated]):
            return

    args = list(node.args)
    args[2] = torch.int32
    node.args = tuple(args)