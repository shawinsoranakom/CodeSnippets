def get_stack_traces(self) -> OrderedSet[str]:
        # Return stack traces to user model code
        # A single IRNode could correspond to multiple lines of code
        stack_traces: OrderedSet[str] = OrderedSet()
        origins = self.origins
        if isinstance(self, ExternKernel):
            origin_node = self.get_origin_node()
            if self.origin_node:
                origins = OrderedSet([origin_node])
        for node in origins:
            if hasattr(node, "stack_trace") and node.stack_trace:
                # nodes in the backward graph don't have mapping to pre_grad_graph
                stack_traces.add(node.stack_trace)
            else:
                pre_grad_nodes = (
                    torch._inductor.debug._inductor_post_to_pre_grad_nodes.get(
                        "postToPre",
                        {},
                        # pyrefly: ignore [missing-attribute]
                    ).get(node.name, [])
                )
                if not isinstance(pre_grad_nodes, list):
                    continue
                for node_name in pre_grad_nodes:
                    stack_trace = (
                        torch._inductor.debug._inductor_pre_grad_node_stack_trace.get(
                            node_name, None
                        )
                    )
                    if stack_trace:
                        stack_traces.add(stack_trace)
        return stack_traces