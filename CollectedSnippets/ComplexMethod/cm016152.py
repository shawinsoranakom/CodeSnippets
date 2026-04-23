def skip_operator(operator):
    nyi_strings = (
        "aten.gather.default",
        "nll_loss",
        "aten.index",
        "aten.scatter_",
        "masked_fill_.Scalar",
    )

    if any(nyi_string in str(operator) for nyi_string in nyi_strings):
        # maybe disable aten.native_layer_norm.default
        # TODO - inputs cannot be randomly initialized, causes cyda failures
        print(f"Skipping {operator}, input generator nyi")
        return True

    # not covered by other non-compute operator heuristics
    if operator == torch.ops.aten._unsafe_view.default:
        print(f"Skipping {operator}, non compute operator")
        return True

    # some of inductor registered to the OpOverload, some registered to OpOverloadPacket
    op_impls = [operator]
    if isinstance(operator, torch._ops.OpOverload):
        op_impls.append(operator.overloadpacket)

    # TODO - skip benchmarking fallbacks. for some ops we have both lowerings and fallbacks
    # so its not clear just from operator what will be lowered.

    if all(op not in decompositions and op not in lowerings for op in op_impls):
        print(f"Skipping {operator}, no inductor impl")
        return True

    if "convolution" in str(operator):
        return True

    return False