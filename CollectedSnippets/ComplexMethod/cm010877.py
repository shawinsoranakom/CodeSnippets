def get_all_output_and_tangent_nodes(
    g: fx.Graph,
) -> dict[DifferentiableAOTOutput, tuple[fx.Node, fx.Node | None]]:
    """Get all output nodes and their corresponding tangent nodes from a joint graph.

    Similar to get_all_input_and_grad_nodes, but returns output nodes paired with
    their tangent nodes (if they exist). This function traverses the graph to find
    all differentiable outputs and matches them with their corresponding tangent
    inputs used in forward-mode autodiff.

    NB: *all* forward tensor output sare turned, including non-differentiable outputs,
    so you can use this function to perform operations on all outputs.

    Args:
        g: The FX joint graph with descriptors

    Returns:
        A dictionary mapping each DifferentiableAOTOutput descriptor to a tuple
        containing:
        - The output node itself
        - The tangent (input) node if it exists, None otherwise

    Raises:
        RuntimeError: If the joint graph has subclass tensor inputs/outputs; this
        is not supported by API as there is not necessarily a 1-1 correspondence
        between outputs and tangents when subclasses are involved.
    """
    output_index: dict[DifferentiableAOTOutput, tuple[fx.Node, fx.Node | None]] = {}
    for n in g.nodes:
        if n.op == "output":
            desc = n.meta["desc"]
            for sub_n, sub_d in zip(n.args[0], desc):
                # Skip outputs that cannot possibly be differentiable
                if not isinstance(sub_d, DifferentiableAOTOutput):
                    continue
                if isinstance(sub_d, SubclassGetAttrAOTOutput):
                    _raise_autograd_subclass_not_implemented(sub_n, sub_d)

                output_index[sub_d] = (sub_n, None)
    for n in g.nodes:
        if n.op == "placeholder":
            desc = n.meta["desc"]
            if isinstance(desc, SubclassGetAttrAOTInput):
                _raise_autograd_subclass_not_implemented(n, desc)
            if isinstance(desc, TangentAOTInput):
                out, tangent = output_index[desc.output]
                if tangent is not None:
                    raise AssertionError(
                        f"tangent already set for {n}, {desc}, {output_index}"
                    )
                output_index[desc.output] = (out, n)
    return output_index