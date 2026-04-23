def reorder_post_acc_grad_hook_nodes(self) -> None:
        """
        Usage of AOTAutograd causes all the post_acc_grad_hook nodes to get
        pushed to the end of the graph. This differs from eager mode, which
        schedules them as soon as possible. This pass attempts to reorder the
        graph to mimic eager behavior.
        """
        post_acc_grad_hooks = []
        for node in self.fx_tracer.graph.find_nodes(
            op="call_function", target=call_hook
        ):
            if node.kwargs.get("hook_type", None) != "post_acc_grad_hook":
                continue
            post_acc_grad_hooks.append(node)

        # nodes in post_acc_grad_hooks are in topo order. For hooks registered
        # to same node, we should keep their relative order
        for node in reversed(post_acc_grad_hooks):
            getitem_node = node.args[0]
            param_node = node.args[1]  # post_acc_grad_hook handle one param

            # find the corresponding acc_grad node
            acc_grad_node = None
            for n in list(param_node.users.keys()):
                if n.op == "call_function" and n.target is call_accumulate_grad:
                    acc_grad_node = n
                    break

            assert acc_grad_node is not None, (
                "post_acc_grad_hook must have corresponding acc grad node"
            )

            # append post_acc_grad_hook after acc_grad node
            acc_grad_node.append(getitem_node)
            getitem_node.append(node)