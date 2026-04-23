def __call__(self, graph: fx.Graph) -> None:
        count = 0

        target_ops = [torch.ops._C.rotary_embedding.default]
        if hasattr(torch.ops.vllm, "rocm_aiter_triton_rotary_embedding"):
            target_ops.append(torch.ops.vllm.rocm_aiter_triton_rotary_embedding.default)

        for node in graph.nodes:
            if not is_func(node, auto_functionalized):
                continue

            kwargs = node.kwargs
            at_target = node.args[0]

            if at_target in target_ops:
                query = kwargs["query"]
                key = kwargs["key"]
                getitem_nodes = {}
                for user in node.users:
                    if is_func(user, operator.getitem):
                        getitem_nodes[user.args[1]] = user

                if (
                    is_func(query, operator.getitem)
                    and is_func(key, operator.getitem)
                    and query.args[0] == key.args[0]
                    and is_func(query.args[0], torch.ops.aten.split_with_sizes.default)
                    and all(
                        is_func(user, torch.ops.aten.slice_scatter.default)
                        for getitem_node in getitem_nodes.values()
                        for user in getitem_node.users
                    )
                ):
                    # Pattern where query and key are slices of a qkv tensor.
                    # While functionalized, results at [1] and [2] are scattered
                    # back into qkv, then split again to get query and key.
                    # If the inplace tensor has no other users, we can replace
                    # the slice_scatter+split nodes with the original results.
                    for user in getitem_nodes[1].users:
                        slice_scatter_1_node = user
                    if not is_func(
                        slice_scatter_1_node, torch.ops.aten.slice_scatter.default
                    ):
                        continue

                    for user in getitem_nodes[2].users:
                        slice_scatter_2_node = user
                    if not is_func(
                        slice_scatter_2_node, torch.ops.aten.slice_scatter.default
                    ):
                        continue

                    for user in slice_scatter_2_node.users:
                        split_node = user
                    if not is_func(split_node, torch.ops.aten.split_with_sizes.default):
                        continue

                    split_getitem_users = {}
                    for user in split_node.users:
                        if is_func(user, operator.getitem):
                            split_getitem_users[user.args[1]] = user

                    # Replace query node
                    split_getitem_users[0].replace_all_uses_with(getitem_nodes[1])
                    graph.erase_node(split_getitem_users[0])
                    # Replace key node
                    split_getitem_users[1].replace_all_uses_with(getitem_nodes[2])
                    graph.erase_node(split_getitem_users[1])
                    # Redirect value node to original qkv tensor
                    split_getitem_users[2].replace_input_with(split_node, query.args[0])

                    # Erase unused nodes
                    graph.erase_node(split_node)
                    graph.erase_node(slice_scatter_2_node)
                    graph.erase_node(slice_scatter_1_node)

                    count += 1

        logger.debug("Eliminated %d slice_scatter+split nodes", count)