def _remove_effect_tokens(ep: ExportedProgram) -> ExportedProgram:
    """
    Removes the existence of tokens from the exported program, including:
    - Removes the input and output tokens
    - Replaces with_effects(token, func, args) with just func(args)

    This function does an inplace modification on the given ExportedProgram.
    """
    inputs_to_lifted_custom_objs = ep.graph_signature.inputs_to_lifted_custom_objs

    # mark submodules with effects as having effects. This will be used in the following pass to remove effects from subgraphs
    for _, module in ep.graph_module.named_modules():
        if not isinstance(module, torch.fx.GraphModule):
            continue

        with_effect_nodes = [
            node for node in module.graph.nodes if node.target is with_effects
        ]
        if len(with_effect_nodes) > 0:
            module.meta["has_with_effects"] = True

    # Process each module with the replace hook to ensure graph signature is updated
    with ep.graph_module._set_replace_hook(ep.graph_signature.get_replace_hook()):
        for _, module in ep.graph_module.named_modules():
            if not isinstance(module, torch.fx.GraphModule):
                continue

            input_tokens = []
            output_tokens = []

            # Process with_effects and invoke_subgraph nodes
            for node in module.graph.nodes:
                if node.target is with_effects:
                    _replace_with_effects_node(
                        node,
                        ep,
                        inputs_to_lifted_custom_objs,
                        output_tokens,
                        input_tokens,
                        module,
                    )
                elif node.target is torch.ops.higher_order.invoke_subgraph:
                    _replace_invoke_subgraph_node(
                        node, module, output_tokens, input_tokens
                    )

            # Remove tokens from the output node
            if len(output_tokens) > 0:
                output_node = next(reversed(module.graph.find_nodes(op="output")))
                output_args = output_node.args[0]
                if len(output_args) < len(output_tokens):
                    raise AssertionError(
                        f"{output_args} output arguments found\n"
                        f"{output_tokens} output tokens found\n"
                        f"{module.graph}"
                    )
                output_node.args = (tuple(output_args[len(output_tokens) :]),)

            module.graph.eliminate_dead_code()

            # Remove tokens from the input placeholders
            for node in module.graph.nodes:
                if node.op == "placeholder" and node in input_tokens:
                    module.graph.erase_node(node)

            module.recompile()

    num_tokens: int = 0
    input_token_names: list[str] = []
    new_input_specs: list[InputSpec] = []
    for inp in ep.graph_signature.input_specs:
        if inp.kind == InputKind.TOKEN:
            num_tokens += 1
            if not isinstance(inp.arg, TokenArgument):
                raise AssertionError(
                    f"Expected inp.arg to be a TokenArgument, but got {type(inp.arg)}"
                )
            input_token_names.append(inp.arg.name)
        else:
            new_input_specs.append(inp)

    num_out_tokens: int = 0
    new_output_specs: list[OutputSpec] = []
    output_token_names: list[OutputSpec] = []
    for out in ep.graph_signature.output_specs:
        if out.kind == OutputKind.TOKEN:
            num_out_tokens += 1
            output_token_names.append(out.arg.name)
        else:
            new_output_specs.append(out)

    # Update graph signature
    ep.graph_signature.input_specs = new_input_specs
    ep.graph_signature.output_specs = new_output_specs

    if num_tokens != num_out_tokens:
        raise AssertionError(
            f"Number of input tokens ({num_tokens}) does not match output tokens ({num_out_tokens})"
        )

    return ep