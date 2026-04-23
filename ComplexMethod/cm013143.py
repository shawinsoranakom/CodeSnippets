def autoDiffErrorMessage(self, should_autodiff_node, nodes_not_in_diff_graph,
                             fusion_nodes_not_found, non_fusible_nodes_being_fused,
                             fusion_nodes_found, nodes_in_diff_graph):
        err_msg = "\nFailure in testing nodes' autodifferentiation. "
        if should_autodiff_node:
            err_msg += "One or more nodes were expected to be autodiffed, " \
                "but were not found in specified fusible/nonfusible " \
                "DifferentiableGraph groups. \nSpecifically:"
            # The node is intended to appear in a differentiable graph but doesn't
            diff_nodes_missing = []
            # The node is intended to appear in a differentiable graph
            # outside of a fusion group but instead is in a fusion group
            diff_nodes_in_fusion = []
            # The node is intended to appear in a fusion group but doesn't
            fusion_nodes_missing = []
            # The node is intended to appear in a fusion group but instead
            # is just in an outer differentiable graph
            fusion_nodes_in_diff = []
            for node in nodes_not_in_diff_graph:
                if node in non_fusible_nodes_being_fused:
                    diff_nodes_in_fusion.append(node)
                else:
                    diff_nodes_missing.append(node)
            for node in fusion_nodes_not_found:
                if node in nodes_in_diff_graph:
                    fusion_nodes_in_diff.append(node)
                else:
                    fusion_nodes_missing.append(node)
            if len(diff_nodes_missing) > 0:
                err_msg += f"\n  {diff_nodes_missing} were not in one of the " \
                    "DifferentiableGraphs when they were expected to be. " \
                    "Did you intend for these nodes to be autodiffed? " \
                    "If not, remove them from the list of nonfusible nodes."
            if len(diff_nodes_in_fusion) > 0:
                err_msg += f"\n  {diff_nodes_in_fusion} were found in one of the FusionGroups " \
                    "when they were expected to be just in a DifferentiableGraph. If it was " \
                    "intended for these nodes to be in FusionGroups, reclassify these nodes as " \
                    "fusible nodes. If these nodes were not intended to be fused, your " \
                    "autodifferentiation logic might be wrong."
            if len(fusion_nodes_missing) > 0:
                err_msg += f"\n  {fusion_nodes_missing} were not in one of the FusionGroups " \
                    "of the DifferentiableGraphs when they were expected to be. " \
                    "They were also not found in an outer DifferentiableGraph. Did you " \
                    "intend for these nodes to be autodifferentiated? If not, you should " \
                    "remove these nodes from the test's fusible nodes. Otherwise your " \
                    "autodifferentiation logic might be wrong."
            if len(fusion_nodes_in_diff) > 0:
                err_msg += f"\n  {fusion_nodes_in_diff} were not in one of the FusionGroups " \
                    "of the DifferentiableGraphs when they were expected to be, " \
                    "instead they were found just in an outer DifferentiableGraph. " \
                    "Did you intend for these nodes to be fused? If not, you should " \
                    "move these nodes into the test's nonfusible nodes. Otherwise your " \
                    "autodifferentiation logic might be wrong."
        else:
            err_msg += "One or more nodes were not expected to be autodiffed " \
                "but were found in a DifferentiableGraph or in a FusionGroup " \
                "of a DifferentiableGraph. Did you intend for these nodes to be " \
                "autodiffed? If so, change this test to expect autodifferentiation. " \
                "\nSpecifically:"
            if len(fusion_nodes_found) > 0:
                err_msg += f"\n  {fusion_nodes_found} were not expected to be in " \
                    "one of the DifferentiableGraphs, but appeared in a FusionGroup " \
                    "of a DifferentiableGraph. "
            if len(nodes_in_diff_graph) > 0:
                err_msg += f"\n  {nodes_in_diff_graph} were not expected to " \
                    "be in one of the DifferentiableGraphs but were."
        return err_msg