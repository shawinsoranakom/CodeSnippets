def get_decompositions(
    aten_ops: Sequence[torch._ops.OperatorBase | OpOverloadPacket],
    type: str = "post_autograd",
) -> dict[torch._ops.OperatorBase, Callable]:
    """
    Retrieve a dictionary of decompositions corresponding to the list of
    operator overloads and overload packets passed as input.  Overload
    packets will include all decomposed overloads in the packet.  If there is
    no decomposition for a requested operator, it is silently ignored.

    This API is experimental; we are almost certainly going to give an alternate,
    more recommended formulation, where a user provides the set of operators
    they know how to implement, and we provide decompositions for everything
    not in this set.
    """
    if type not in {"post_autograd", "pre_autograd", "meta"}:
        raise AssertionError(
            f"type must be one of post_autograd, pre_autograd, or meta, got {type}"
        )

    registry = global_decomposition_table[type]
    packets_to_overloads = defaultdict(list)

    for opo in registry:
        if isinstance(opo, (OpOverload, OpOverloadPacket)):
            packets_to_overloads[opo.overloadpacket].append(opo)
    decompositions: dict[torch._ops.OperatorBase, Callable] = {}
    for op in aten_ops:
        if isinstance(op, OpOverloadPacket) and op in packets_to_overloads:
            for op_overload in packets_to_overloads[op]:
                decompositions[op_overload] = registry[op_overload]
        elif isinstance(op, (torch._ops.OperatorBase)) and op in registry:
            decompositions[op] = registry[op]
    return decompositions