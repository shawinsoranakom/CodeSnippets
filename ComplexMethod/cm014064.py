def reorder_post_hook_nodes(self) -> None:
        """
        Usage of AOTAutograd causes all the post_hook nodes to get pushed to the
        end of the graph. This differs from eager mode, which schedules them as
        soon as possible. This pass attempts to reorder the graph to mimic eager
        behavior.
        """
        post_hooks = []
        for node in self.fx_tracer.graph.find_nodes(
            op="call_function", target=call_hook
        ):
            if node.kwargs.get("hook_type", None) != "post_hook":
                continue
            post_hooks.append(node)

        for node in reversed(post_hooks):
            getitem_node = node.args[0]
            output_nodes = node.args[1]
            input_nodes = node.args[2]

            if len(output_nodes) > 0:
                continue

            # pyrefly: ignore [implicit-any]
            input_nodes_and_users = []
            input_nodes_and_users.extend(list(input_nodes))
            for input_node in input_nodes:
                input_nodes_and_users.extend(
                    user
                    for user in list(input_node.users.keys())
                    if not (
                        user.op == "call_function"
                        and user.target is call_hook
                        and node.kwargs.get("hook_type", None) == "post_hook"
                    )
                )

            arg = max(input_nodes_and_users)  # last input users
            if arg.op == "call_function" and arg.target is call_accumulate_grad:
                param_node = arg.args[0]
                post_acc_grad_hook_node = None
                for n in list(param_node.users.keys()):
                    if (
                        n.op == "call_function"
                        and n.target is call_hook
                        and n.kwargs.get("hook_type", None) == "post_acc_grad_hook"
                    ):
                        post_acc_grad_hook_node = n

                if post_acc_grad_hook_node is not None:
                    post_acc_grad_hook_node.append(getitem_node)
                    getitem_node.append(node)
                    continue

            if arg is not node.prev and not self.is_placeholder(arg):
                arg.append(getitem_node)
                getitem_node.append(node)