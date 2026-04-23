def _unlift_tokens_from_module_helper(
        module: torch.fx.GraphModule,
        subgraph_str: str,
        expected_num_erased: int | None,
    ) -> None:
        input_token_nodes = set()
        output_token_nodes = set()

        for node in module.graph.nodes:
            if (
                node.op == "call_function"
                and node.target is torch.ops.higher_order.with_effects
            ):
                if node.args[0].op == "placeholder":
                    input_token_nodes.add(node.args[0])
                    replace_input_token_with_make_token(module, node.args[0])

                tokens_from_with_effects = get_output_tokens(node)
                output_token_nodes = output_token_nodes | tokens_from_with_effects

            elif (
                node.op == "call_function"
                and node.target is torch.ops.higher_order.invoke_subgraph
            ):
                subgraph_node, identifier, *operands = node.args

                # Check if subgraph has effects by looking in the cache
                from torch._guards import InvokeSubgraphCache, TracingContext

                effects = None
                tracing_ctx = TracingContext.try_get()
                if tracing_ctx:
                    invoke_subgraph_cache = (
                        tracing_ctx.hop_dispatch_set_cache.get_cache(
                            torch.ops.higher_order.invoke_subgraph
                        )
                    )
                    if invoke_subgraph_cache:
                        if not isinstance(invoke_subgraph_cache, InvokeSubgraphCache):
                            raise AssertionError(
                                f"expected InvokeSubgraphCache, got {type(invoke_subgraph_cache)}"
                            )
                        effects = invoke_subgraph_cache.get_effects(identifier)

                if effects is not None:
                    # Wrap invoke_subgraph with with_effects
                    # Before: invoke_subgraph(subgraph, id, token, *args) -> (token_out, result)
                    # After: with_effects(token, invoke_subgraph, subgraph, id, *args) -> (token_out, result)
                    #
                    # Note: The subgraph itself will be unlifted separately when we iterate
                    # through named_modules() below.

                    num_tokens = len(effects)
                    if num_tokens != 1:
                        raise AssertionError(
                            f"Multiple token subgraph NYI, got {num_tokens} tokens"
                        )
                    token_args = operands[:num_tokens]
                    non_token_args = operands[num_tokens:]

                    # Create with_effects wrapper around invoke_subgraph
                    # with_effects(token, op, *args) where op is invoke_subgraph
                    # Pass the subgraph and non-token args to invoke_subgraph
                    with module.graph.inserting_before(node):
                        new_node = module.graph.call_function(
                            torch.ops.higher_order.with_effects,
                            # pyrefly: ignore [bad-argument-type]
                            (
                                token_args[0],  # pyrefly: ignore[bad-argument-type]
                                torch.ops.higher_order.invoke_subgraph,
                                subgraph_node,
                                identifier,
                                *tuple(non_token_args),
                            ),
                        )
                        node.replace_all_uses_with(new_node)
                        new_node.meta = node.meta
                        module.graph.erase_node(node)

                    for token in token_args:
                        if token.op == "placeholder":
                            input_token_nodes.add(token)
                            replace_input_token_with_make_token(module, token)

                    # Get output tokens from the new with_effects node
                    tokens_from_invoke_subgraph = get_output_tokens(new_node)
                    output_token_nodes = (
                        output_token_nodes | tokens_from_invoke_subgraph
                    )

        if not output_token_nodes and not input_token_nodes:
            return

        output_node = next(reversed(module.graph.find_nodes(op="output")))
        if output_node is None:
            raise AssertionError("output node not found in graph")
        with module.graph.inserting_before(output_node):
            module.graph.call_function(
                torch.ops.prims._sink_tokens.default,
                (list(output_token_nodes),),
            )
        new_out_args = tuple(
            [out for out in output_node.args[0] if out not in output_token_nodes]
        )
        output_node.args = (new_out_args,)

        if expected_num_erased:
            if len(input_token_nodes) != expected_num_erased:
                raise AssertionError(
                    f"{subgraph_str} num_erased_inputs:{len(input_token_nodes)} "
                    f"{input_token_nodes} != expected {expected_num_erased} \n"
                    f"{fw_module.print_readable(print_output=False)}"
                )
            if len(output_token_nodes) != expected_num_erased:
                raise AssertionError(
                    f"{subgraph_str} num_erased_outs:{len(output_token_nodes)} "
                    f"{output_token_nodes} != expected {expected_num_erased} \n"
                    f"{fw_module.print_readable(print_output=False)}"
                )

        module.recompile()