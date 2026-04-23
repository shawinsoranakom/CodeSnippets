def reorder_pre_hook_nodes_to_schedule_asap(self) -> None:
        """
        In this function, we schedule the pre hooks as soon as possible. This
        does not match eager behavior (schedule pre hook right before its
        registered node), but it can make acc grad be scheduled properly when
        the pre hooks are registered to them. After reordering acc grad node, we
        will reorder the pre hooks again to mimic eager behavior.
        """
        for node in self.fx_tracer.graph.find_nodes(
            op="call_function", target=call_hook
        ):
            if node.kwargs.get("hook_type", None) != "pre_hook":
                continue

            getitem_node = node.args[0]
            # pre_hook handle a tuple of grad tensors
            input_nodes = self.get_all_nodes(node.args[1])

            to_remove = []
            to_append = []
            hook_block = [node]  # contain the hook and hook args getitem
            for n in input_nodes:
                if n.op == "call_function" and n.target is operator.getitem:
                    to_append.append(n.args[0])
                    to_remove.append(n)
                    hook_block.append(n)
            for a, b in zip(to_remove, to_append):
                input_nodes.remove(a)
                input_nodes.append(b)  # type: ignore[arg-type]

            arg = max(input_nodes)  # last input
            if arg is not node.prev and not self.is_placeholder(arg):
                arg.append(getitem_node)
                for n in hook_block:
                    getitem_node.append(n)