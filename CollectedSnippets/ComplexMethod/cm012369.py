def _categorize_subgraph_nodes(self) -> None:
        """
        For each chunked node, decide if it's a input/body/output node of the
        chunking subgraph.
        """
        for node in self.parent_graph.nodes:
            meta = get_chunking_meta(node)

            # The node does not have chunking metadata, skip
            if meta is None:
                continue

            # skip tangent nodes since they are overridden as 1 and
            # reapplied later in the bwd graph
            if is_tangent_node(node):
                self.overriden_tangent[node] = None  # will update the value later
                continue

            # To check if a node is a placeholder for the chunking
            # subgraph there are 2 alternatives
            # 1. decide it's a placeholder if it's using any non-chunked node as argument
            # 2. decide it's a placeholder if it's not using any chunked nodes as argument
            # These 2 rules are almost equivalent since we don't mix
            # chunked and non-chunked arguments for a fx.Node.
            # But one subtle difference is for aten.full node.
            # We don't need to pass in aten.full as a placeholder since
            # we can just add the chunked aten.full in the subgraph
            # directly.
            # Alternative 2 does not work for this case, so we implement
            # alternative 1.

            user_nodes = node.users
            user_nodes_no_meta = [
                node for node in user_nodes if get_chunking_meta(node) is None
            ]

            if is_chunking_subgraph_input(node):
                # None of the node's arguments are chunked. It's a placeholder
                self.subgraph_input.append(node)
            elif len(user_nodes_no_meta) > 0:
                self.subgraph_output.append(node)
            else:
                self.subgraph_body.append(node)

        assert len(self.subgraph_body) > 0