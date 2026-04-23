def reorder_pre_hook_nodes_to_mimic_eager(self) -> None:
        """
        Usage of AOTAutograd causes all the pre_hook nodes to get pushed to the
        end of the graph. This differs from eager mode, which schedules them
        right before their registered node execution. This pass attempts to
        reorder the graph to mimic eager behavior.
        """
        pre_hooks = []
        for node in self.fx_tracer.graph.find_nodes(
            op="call_function", target=call_hook
        ):
            if node.kwargs.get("hook_type", None) != "pre_hook":
                continue
            pre_hooks.append(node)

        for node in reversed(pre_hooks):
            hook_getitem_node = node.args[0]

            users = list(node.users.keys())
            if len(users) == 0:
                continue

            # users are all getitem ops and they are used by same registered node
            assert all(
                user.op == "call_function" and user.target is operator.getitem
                for user in users
            )
            registered_node = next(iter(users[0].users.keys()))

            if registered_node is not node.next:
                registered_node.prepend(hook_getitem_node)
                registered_node.prepend(node)
                for getitem in users:
                    registered_node.prepend(getitem)