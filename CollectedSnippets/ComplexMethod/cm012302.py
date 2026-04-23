def visit(other_node):
        if (
            other_node.op == "call_function"
            and other_node.target != operator.getitem
            and all((n in seen_nodes) for n in other_node.users)
            and get_mutation_region_id(graph, node)
            == get_mutation_region_id(graph, other_node)
            and check()
        ):
            # Ops that consume RNG state are order-sensitive and must not be
            # reordered during locality optimization.
            if consumes_rng_state(other_node):
                return

            # move node's producers right before it
            node.prepend(other_node)