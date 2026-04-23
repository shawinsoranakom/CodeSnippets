def move_reshape_out_of_split_stack(match: Match, *args, **kwargs):
    split_node = next(node for node in match.nodes if node.target is torch.split)
    split_dim = _get_dim(split_node)
    split_users = list(split_node.users.keys())
    stack_nodes = [node for node in match.nodes if node.target is torch.stack]
    graph = match.graph
    threshold_to_cat = torch._inductor.config.pre_grad_fusion_options[
        "move_reshape_out_of_split_stack_pass"
    ].get("threshold_to_cat", 10)
    for stack_node in stack_nodes:
        if not is_node_meta_valid(stack_node):
            log.debug("example value absent for node: %s", stack_node)
            continue
        stack_dim = _get_dim(stack_node)
        stack_inputs = get_arg_value(stack_node, 0, "tensors")  # type: ignore[union-attr]
        inputs = []
        for stack_input in stack_inputs:
            if stack_input.target != torch.reshape:
                inputs.append(stack_input)
            else:
                inputs.append(stack_input.args[0])  # type: ignore[union-attr]
        new_cat_args, _new_cat_args_meta = construct_cat_args(
            graph,
            stack_node,
            inputs,
            split_node,
            threshold_to_cat,
            update_args_from_split_getitem,
        )
        # At least one node would be in the returned new_cat_args
        # case 1: only one node in the new cat args, don't need to cat
        if len(new_cat_args) == 1:
            reshape_node = convert_reshape_cat_arg_to_stack(
                graph,
                new_cat_args[0],
                stack_node,
                stack_node.meta["example_value"].shape,
                stack_dim,
                split_dim,
            )
            stack_node.replace_all_uses_with(reshape_node)
            # remove stack node
            graph.erase_node(stack_node)
            # check the input of stack node, and remove nodes that have no users
            remove_split_unbind_children(graph, stack_inputs)  # type: ignore[arg-type]
            remove_split_unbind_children(graph, split_users)  # type: ignore[arg-type]
            counters[backend]["move_reshape_out_of_split_stack_pass"] += 1
            continue
        if len(new_cat_args) > 1 and len(new_cat_args) < len(inputs):
            # decompose the cat args into multiple stack nodes, i.e., we stack
            # all the nodes exist in the stack inputs and reshape the rest followed by a cat
            stack_node_input, stack_node_input_meta, cat_inputs = [], [], []  # type: ignore[var-annotated]
            for cat_arg in new_cat_args:
                if cat_arg not in stack_inputs:
                    if len(stack_node_input) > 0:
                        with graph.inserting_after(stack_node):
                            decomposed_stack_node = graph.call_function(
                                torch.stack,
                                args=(stack_node_input,),
                                kwargs={"dim": stack_dim},
                            )
                            decomposed_stack_node.meta["example_value"] = torch.stack(
                                stack_node_input_meta, dim=stack_dim
                            )
                            cat_inputs.append(decomposed_stack_node)
                    # cat_arg must be the split input
                    view_shape_list = get_view_shape_list(cat_arg, stack_dim)
                    stack_node_shape = torch.reshape(
                        cat_arg.meta["example_value"], tuple(view_shape_list)
                    ).shape  # type: ignore[union-attr]
                    cat_inputs.append(
                        convert_reshape_cat_arg_to_stack(
                            graph,
                            cat_arg,
                            stack_node,
                            stack_node_shape,
                            stack_dim,
                            split_dim,
                        )
                    )
                    stack_node_input, stack_node_input_meta = [], []
                else:
                    stack_node_input.append(cat_arg)
                    stack_node_input_meta.append(cat_arg.meta["example_value"])

            if len(stack_node_input) > 0:
                with graph.inserting_after(stack_node):
                    decomposed_stack_node = graph.call_function(
                        torch.stack,
                        args=(stack_node_input,),
                        kwargs={"dim": stack_dim},
                    )
                    decomposed_stack_node.meta["example_value"] = torch.stack(
                        stack_node_input_meta, dim=stack_dim
                    )
                    cat_inputs.append(decomposed_stack_node)

            with graph.inserting_after(stack_node):
                cat_node = graph.call_function(
                    torch.cat,
                    args=(cat_inputs,),
                    kwargs={"dim": stack_dim},
                )
                stack_node.replace_all_uses_with(cat_node)
                cat_node.meta.update(stack_node.meta)
                graph.erase_node(stack_node)
                remove_split_unbind_children(graph, stack_inputs)  # type: ignore[arg-type]
                remove_split_unbind_children(graph, split_users)  # type: ignore[arg-type]
            counters[backend]["move_reshape_out_of_split_stack_pass"] += 1