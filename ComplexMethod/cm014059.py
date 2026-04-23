def move_graph_nodes_to_cuda(self, graph: torch.fx.Graph) -> list[int]:
        to_move: dict[int, torch.fx.Node] = {}
        has_cuda_inputs = False
        nodes = list(graph.nodes)
        assert nodes[0].target == "inputs"
        inputs = nodes[0]
        inputs_users = list(inputs.users.keys())
        # input access nodes should immediately follow placeholder nodes
        first_getitem_idx = len(_graph_placeholders)
        assert nodes[first_getitem_idx] == inputs_users[0]
        last_getitem_idx = first_getitem_idx + len(inputs_users) - 1
        assert nodes[last_getitem_idx] == inputs_users[-1]
        # getitem nodes on inputs
        for i, node in enumerate(inputs_users):
            if not has_cuda_inputs and node.meta["val"].device.type == "cuda":
                has_cuda_inputs = True
                continue

            is_cpu = node.meta["val"].device.type == "cpu"
            is_scalar = len(node.meta["val"].size()) == 0
            if is_cpu and is_scalar:
                node_users = list(node.users.keys())
                # We can only move the cpu scalar if it is not exposed to user code.
                if all(
                    (
                        isinstance(user.target, torch._ops.OpOverload)
                        and user.target.namespace in ("prims", "aten")
                    )
                    or (
                        isinstance(user.target, Op)
                        and not user.target.is_custom_function
                    )
                    for user in node_users
                ):
                    # all users are prims/aten, can move safely
                    to_move[i] = node

        # only move cpu scalars to cuda if there were cuda activations in this graph,
        # this is to handle the case where cudagraphs is enabled on a cpu-only graph
        if has_cuda_inputs:
            for node in to_move.values():
                verbose_log.debug("Moving node %s from cpu to cuda", node)
                node.meta["val"] = node.meta["val"].cuda()

            # return runtime indices we need to move to cuda
            return list(to_move.keys())

        return []