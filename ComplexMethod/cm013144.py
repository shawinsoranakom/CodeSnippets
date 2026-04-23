def assertAutodiffNode(self, graph, should_autodiff_node, nonfusible_nodes, fusible_nodes):
        diff_nodes = graph.findAllNodes('prim::DifferentiableGraph')
        diff_subgraphs = [node.g('Subgraph') for node in diff_nodes]

        # Note: currently no tests have fusible_nodes
        fusion_nodes = list(chain.from_iterable([g.findAllNodes('prim::FusionGroup') for g in diff_subgraphs]))
        fusion_subgraphs = [node.g('Subgraph') for node in fusion_nodes]

        # For any non-fusible node, it must show up in one of the DifferentiableGraphs.
        nodes_in_diff_graph = []
        nodes_not_in_diff_graph = []
        non_fusible_nodes_being_fused = []
        for node in nonfusible_nodes:
            if any(g.findNode(node) is not None for g in diff_subgraphs):
                nodes_in_diff_graph.append(node)
            else:
                nodes_not_in_diff_graph.append(node)
            if any(g.findNode(node) is not None for g in fusion_subgraphs):
                non_fusible_nodes_being_fused.append(node)
        found_all_nonfusible_nodes = len(nodes_in_diff_graph) == len(nonfusible_nodes)

        # For any fusible node, it must show up in one of the FusionGroups in one of the DifferentiableGraphs.
        fusion_nodes_found = []
        fusion_nodes_not_found = []
        for node in fusible_nodes:
            if any(g.findNode(node) is not None for g in fusion_subgraphs):
                fusion_nodes_found.append(node)
            else:
                fusion_nodes_not_found.append(node)
        found_all_fusible_nodes = len(fusion_nodes_found) == len(fusible_nodes)

        if should_autodiff_node is not None:
            err_msg = self.autoDiffErrorMessage(should_autodiff_node,
                                                nodes_not_in_diff_graph,
                                                fusion_nodes_not_found,
                                                non_fusible_nodes_being_fused,
                                                fusion_nodes_found,
                                                nodes_in_diff_graph)
            self.assertEqual(should_autodiff_node,
                             found_all_nonfusible_nodes and found_all_fusible_nodes, err_msg)