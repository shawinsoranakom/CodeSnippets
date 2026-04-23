def _order_nodes(node_a, node_b, node_c) -> list[Node]:
                nodes = [node_a, node_b, node_c]
                first_node = None
                mid_node = None
                last_node = None
                for n in nodes:
                    prev_n = n.args[0]
                    next_n = next(iter(n.users))
                    if prev_n not in nodes:
                        first_node = n
                    elif next_n not in nodes:
                        last_node = n
                    else:
                        mid_node = n
                if first_node is None or mid_node is None or last_node is None:
                    raise AssertionError("Expected all nodes to be non-None")
                if mid_node.args[0] is not first_node:
                    raise AssertionError("Expected mid_node.args[0] to be first_node")
                if last_node.args[0] is not mid_node:
                    raise AssertionError("Expected last_node.args[0] to be mid_node")
                return [last_node, mid_node, first_node]