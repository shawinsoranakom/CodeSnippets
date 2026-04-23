def replace_cat(
        self,
        graph: torch.fx.Graph,
        split_node: torch.fx.Node,
        next_users: list[torch.fx.Node],
        user_inputs_list_new,
        transform_params_list: list[list[_TransformParam]],
    ):
        split_dim = _get_dim(split_node)
        split_users = split_node.users.keys()
        new_cats = []
        for user_node, user_inputs_new, transform_params in zip(
            next_users, user_inputs_list_new, transform_params_list
        ):
            if user_node.target not in (torch.cat, torch.stack):
                # Change the args and kwargs of non-cat/stack nodes. Replace old getitems (belonging to
                # the original split node) with the newer getitems
                next_cat_input = 0
                for input_node in user_node.all_input_nodes:
                    if input_node in split_users:
                        user_node.replace_input_with(
                            input_node, user_inputs_new[next_cat_input]
                        )
                        next_cat_input += 1
                continue

            # Handle cat/stack user nodes
            cat_dim = get_arg_value(user_node, 1, "dim")
            user_inputs_new_transformed, user_inputs_new_transformed_meta = [], []
            # For `unsqueeze` transform, we will combine consecutive inputs with the same unsqueeze params, and stack them
            to_stack, to_stack_meta = [], []
            stack_dim = None
            with graph.inserting_before(user_node):
                # pyrefly: ignore [bad-assignment]
                for user_input_new, transform_param in zip(
                    user_inputs_new, transform_params
                ):
                    # pyrefly: ignore [bad-argument-type]
                    if not is_node_meta_valid(user_input_new):
                        log.debug("example value absent for node: %s", user_input_new)
                        return
                    # Apply transforms
                    (
                        unflatten_params,
                        movedim_params,
                        unsqueeze_params,
                        flatten_params,
                    ) = transform_param
                    if unsqueeze_params and (
                        stack_dim is None or stack_dim == unsqueeze_params[0]
                    ):
                        to_stack.append(user_input_new)
                        # pyrefly: ignore [missing-attribute]
                        to_stack_meta.append(user_input_new.meta["example_value"])
                        stack_dim = unsqueeze_params[0]
                        continue
                    elif to_stack:
                        stacked_input = graph.call_function(
                            torch.stack, args=(to_stack,), kwargs={"dim": stack_dim}
                        )
                        stacked_input.meta["example_value"] = torch.stack(  # type: ignore[arg-type]
                            to_stack_meta,
                            dim=stack_dim,  # type: ignore[arg-type]
                        )
                        to_stack, to_stack_meta = [], []
                        stack_dim = None
                        user_inputs_new_transformed.append(stacked_input)
                        user_inputs_new_transformed_meta.append(
                            stacked_input.meta["example_value"]
                        )
                        if unsqueeze_params:
                            to_stack.append(user_input_new)
                            stack_dim = unsqueeze_params[0]
                            # pyrefly: ignore [missing-attribute]
                            to_stack_meta.append(user_input_new.meta["example_value"])
                            continue

                    if unflatten_params:
                        # pyrefly: ignore [missing-attribute]
                        user_input_new_meta = user_input_new.meta["example_value"]
                        user_input_new = graph.call_function(
                            torch.unflatten, args=(user_input_new, *unflatten_params)
                        )
                        user_input_new.meta["example_value"] = torch.unflatten(  # type: ignore[arg-type]
                            user_input_new_meta,  # type: ignore[arg-type]
                            *unflatten_params,  # type: ignore[arg-type]
                        )
                    if movedim_params:
                        # pyrefly: ignore [missing-attribute]
                        user_input_new_meta = user_input_new.meta["example_value"]
                        user_input_new = graph.call_function(
                            torch.movedim, args=(user_input_new, *movedim_params)
                        )
                        user_input_new.meta["example_value"] = torch.movedim(  # type: ignore[arg-type]
                            user_input_new_meta,  # type: ignore[arg-type]
                            *movedim_params,  # type: ignore[arg-type]
                        )
                    if flatten_params:
                        # pyrefly: ignore [missing-attribute]
                        user_input_new_meta = user_input_new.meta["example_value"]
                        user_input_new = graph.call_function(
                            torch.flatten, args=(user_input_new, *flatten_params)
                        )
                        user_input_new.meta["example_value"] = torch.flatten(  # type: ignore[arg-type]
                            user_input_new_meta,
                            *flatten_params,  # type: ignore[arg-type]
                        )
                    user_inputs_new_transformed.append(user_input_new)
                    user_inputs_new_transformed_meta.append(
                        # pyrefly: ignore [missing-attribute]
                        user_input_new.meta["example_value"]
                    )
                if to_stack:
                    stacked_input = graph.call_function(
                        torch.stack, args=(to_stack,), kwargs={"dim": stack_dim}
                    )
                    stacked_input.meta["example_value"] = torch.stack(  # type: ignore[arg-type]
                        to_stack_meta,
                        dim=stack_dim,  # type: ignore[arg-type]
                    )
                    user_inputs_new_transformed.append(stacked_input)
                    user_inputs_new_transformed_meta.append(
                        stacked_input.meta["example_value"]
                    )

            with graph.inserting_after(user_node):
                if len(user_inputs_new_transformed) > 1:
                    new_cat_node = graph.call_function(
                        torch.cat,
                        args=(user_inputs_new_transformed,),
                        kwargs={"dim": cat_dim},
                    )
                    new_cat_node.meta["example_value"] = torch.cat(
                        user_inputs_new_transformed_meta,
                        dim=cat_dim,
                    )
                    counters[backend]["scmerge_cat_added"] += 1
                else:
                    new_cat_node = user_inputs_new_transformed[-1]
                    new_cat_node.meta["example_value"] = (
                        user_inputs_new_transformed_meta[-1]
                    )

            if (
                user_node.target is torch.cat
                and split_dim != cat_dim
                and split_node.target is torch.split
            ):
                with graph.inserting_after(new_cat_node):
                    new_cat_node_meta = new_cat_node.meta["example_value"]
                    new_cat_node = graph.call_function(
                        torch.flatten, args=(new_cat_node, cat_dim, cat_dim + 1)
                    )
                    new_cat_node.meta["example_value"] = torch.flatten(
                        new_cat_node_meta,
                        cat_dim,
                        cat_dim + 1,
                    )
            user_node.replace_all_uses_with(new_cat_node)
            new_cats.append(new_cat_node)