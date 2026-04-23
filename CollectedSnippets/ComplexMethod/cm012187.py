def is_fusible_node(n: fx.Node) -> bool:
    """Check if a node is fusible based on whether it has an inductor lowering.

    A node is fusible if:
    - It has a lowering in torch._inductor.lowering.lowerings
    - It does NOT have a flop counter (expensive compute ops like mm/conv)
    - It is NOT a registered fallback (ops that fall back to eager)
    - It is NOT a collective or wait op
    - For aten.cat, it must have <= max_pointwise_cat_inputs inputs
    """
    if n.op != "call_function":
        return False

    target = n.target
    if not isinstance(target, torch._ops.OpOverload):
        return False

    # Exclude collectives and waits (they have their own scheduling)
    if target.namespace == "_c10d_functional":
        return False

    from torch._inductor.lowering import fallbacks, lowerings
    from torch.utils.flop_counter import flop_registry

    # Must have a lowering
    if target not in lowerings:
        return False

    # Exclude fallbacks (ops that fall back to eager execution)
    if target in fallbacks:
        return False

    # Exclude ops with flop counters (expensive compute ops like mm, conv, etc.)
    overload_packet = target.overloadpacket
    if overload_packet in flop_registry:
        return False

    # Special case: cat is only fusible if it has few enough inputs
    if target == torch.ops.aten.cat.default:
        inputs = n.args[0] if n.args else []
        if isinstance(inputs, (list, tuple)):
            import torch._inductor.config as inductor_config

            if len(inputs) > inductor_config.max_pointwise_cat_inputs:
                return False

    return True