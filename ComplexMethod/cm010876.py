def get_all_input_and_grad_nodes(
    g: fx.Graph,
) -> dict[DifferentiableAOTInput, tuple[fx.Node, fx.Node | None]]:
    """
    Given a joint graph with descriptors (meta['desc'] on placeholders and
    output), returns the node for every input and its corresponding grad
    output node if it exists.  These tuples are in a dict that is indexed by
    the AOTInput descriptor that describes the input.

    NB: *all* forward tensor inputs are returned, including non-differentiable
    inputs (which simply have a None grad), so it is safe to use this function
    to perform operations on all inputs.  (Non-tensor inputs like symbolic
    integers, tokens or RNG state are NOT traversed by this function.)

    Args:
        g: The FX joint graph with descriptors

    Returns:
        A dictionary mapping each DifferentiableAOTInput descriptor to a tuple
        containing:
        - The input node itself
        - The grad (output) node if it exists, None otherwise

    Raises:
        RuntimeError: If the joint graph has subclass tensor inputs/outputs; this
        is not supported by API as there is not necessarily a 1-1 correspondence
        between inputs and grads when subclasses are involved.
    """
    input_index: dict[DifferentiableAOTInput, tuple[fx.Node, fx.Node | None]] = {}
    for n in g.nodes:
        if n.op == "placeholder":
            desc = n.meta["desc"]
            # Skip inputs that cannot possibly be differentiable
            if not isinstance(desc, DifferentiableAOTInput):
                continue
            if isinstance(desc, SubclassGetAttrAOTInput):
                _raise_autograd_subclass_not_implemented(n, desc)

            input_index[desc] = (n, None)
        elif n.op == "output":
            if "desc" not in n.meta:
                raise AssertionError(f"'desc' not in n.meta for {n}: {n.meta}")
            desc = n.meta["desc"]
            for sub_n, sub_desc in zip(n.args[0], desc):
                if isinstance(sub_desc, SubclassGetAttrAOTOutput):
                    _raise_autograd_subclass_not_implemented(sub_n, sub_desc)
                if isinstance(sub_desc, GradAOTOutput):
                    inp, grad = input_index[sub_desc.grad_of]
                    if grad is not None:
                        raise AssertionError(
                            f"grad already set for {sub_n}, {sub_desc}, {input_index}"
                        )
                    input_index[sub_desc.grad_of] = (inp, sub_n)
    return input_index