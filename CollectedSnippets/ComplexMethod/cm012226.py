def get_transform_params(
        self,
        split_node: torch.fx.Node,
        next_users: list[torch.fx.Node],
        user_inputs_list: list[list[torch.fx.Node | _Range]],
    ) -> list[list[_TransformParam]] | None:
        """
        Figure out what transforms are needed for each input to each cat node.

        We replace a split node with an unflatten followed by a movedim
        """
        split_dim = _get_dim(split_node)
        split_sections = split_node.args[1]
        transform_params_list: list[list[_TransformParam]] = []

        for user_node, user_inputs in zip(next_users, user_inputs_list):
            if user_node.target not in (torch.cat, torch.stack):
                transform_params_list.append([])
                continue

            cat_dim = get_arg_value(user_node, 1, "dim")
            transform_params: list[_TransformParam] = []
            for user_input in user_inputs:
                if split_dim == cat_dim and user_node.target is torch.cat:
                    # No transform needed
                    transform_params.append((None, None, None, None))
                elif isinstance(user_input, tuple):  # Split being simplified
                    # Verify equal split
                    subset_split_sections = split_sections[  # type: ignore[index]
                        # pyrefly: ignore [bad-index]
                        user_input[0] : user_input[1]
                        + 1  # type: ignore[index]
                    ]
                    # All sections should be equal
                    if len(OrderedSet(subset_split_sections)) != 1:  # type: ignore[arg-type]
                        return None

                    num_splits = len(subset_split_sections)  # type: ignore[arg-type]
                    unflatten_params = (split_dim, (num_splits, -1))
                    movedim_params = (
                        (split_dim, cat_dim) if split_dim != cat_dim else None
                    )
                    transform_params.append(
                        (unflatten_params, movedim_params, None, None)
                    )
                elif (
                    user_node.target is torch.stack or split_dim != cat_dim
                ):  # We need to unsqueeze inputs not coming through split
                    transform_params.append((None, None, (cat_dim,), None))
                else:  # Non-split inputs
                    transform_params.append((None, None, None, None))
            transform_params_list.append(transform_params)
        return transform_params_list