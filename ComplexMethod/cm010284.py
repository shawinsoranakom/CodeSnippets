def _fix_input_output_signature(
    gm: torch.fx.GraphModule, signature: ModuleCallSignature
) -> None:
    """
    Given the unlifted module from calling ep.module(), we want to remove the
    pytree processing from the graph module's PyTreeCodeGen and instead make it
    nodes inside of the graph. This allows us to do some optimizations, like
    remove these pytree calls if it is unnecessary, and makes the PyTree part
    more obvious to graph passes.
    """
    from torch.export.unflatten import _generate_flatten, _generate_unflatten

    # Remove the registered pytree codegen because we will take care of it
    # through inserting pytree nodes into the graph
    gm.graph._codegen = torch.fx.graph.CodeGen()

    old_placeholders = [node for node in gm.graph.nodes if node.op == "placeholder"]

    new_placeholders = []
    forward_arg_names = signature.forward_arg_names
    if forward_arg_names is None:
        forward_arg_names = []
        if signature.in_spec.num_children != 2:
            raise AssertionError(
                f"Expected in_spec to have 2 children, but got {signature.in_spec.num_children}"
            )
        arg_spec = signature.in_spec.child(0)
        kwarg_spec = signature.in_spec.child(1)
        if arg_spec.type is not tuple:
            raise AssertionError(
                f"Expected arg_spec type to be tuple, but got {arg_spec.type}"
            )
        if kwarg_spec.type is not dict:
            raise AssertionError(
                f"Expected kwarg_spec type to be dict, but got {kwarg_spec.type}"
            )
        for i in range(arg_spec.num_children):
            forward_arg_names.append(f"arg_{i}")
        forward_arg_names.extend(kwarg_spec.context)

    for arg in forward_arg_names:
        with gm.graph.inserting_before(old_placeholders[0]):
            new_placeholders.append(gm.graph.placeholder(arg))

    # Insert flatten call for the inputs
    with gm.graph.inserting_before(old_placeholders[0]):
        flat_node = _generate_flatten(gm, tuple(new_placeholders))
        for i, old_placeholder in enumerate(old_placeholders):
            old_placeholder.op = "call_function"
            old_placeholder.target = operator.getitem
            old_placeholder.args = (flat_node, i)

    # Insert unflatten call for the outputs
    output_node = next(node for node in gm.graph.nodes if node.op == "output")
    with gm.graph.inserting_before(output_node):
        unflat = _generate_unflatten(gm, output_node.args[0], signature.out_spec)
        output_node.args = (unflat,)

    gm.recompile()