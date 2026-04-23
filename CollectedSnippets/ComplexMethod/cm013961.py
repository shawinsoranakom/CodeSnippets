def get_identical_regions(self, graph: torch.fx.Graph) -> list[list[Region]]:
        """
        This function is responsible for extracting the largest regions of identical nodes from the given graph.
        **Note**: This function assumes the nodes that have been tracked with track_node are in the provided graph argument.

        The algorithm proceeds as follows:
        The nodes tracked via track_node above are organized into region groups. The initial region groups look like this:
        [[IdenticalNode1], [IdenticalNode2], [IdenticalNode3]] and each sublist is called a region. For each region group
        (starting at the topologically latest region group), the inner regions are gradually expanded one node at time from
        the flattened args and kwargs of the node in each region provided that for all regions in the group, the nodes being
        added are also identical (ie have the same key computed by track_node). This is checked by verifying that the two
        nodes have the same identical node list in node_to_duplicates.
        """
        topological_ranking = {node: i for i, node in enumerate(graph.nodes)}
        region_groups_with_rank = []
        # needed to detect if replacing a region will create cycles
        node_to_recursive_ancestors = _populate_recursive_ancestor_map(graph)

        # Create region groups; a region group is a group
        # of regions that are all identical. In this initial state
        # each region in the group is a single node, and we discard
        # groups that are only a single region.
        # We track the topological ranking to start with groups later in the graph
        # the reason for this is that we will necessarily create the largest groups first.
        for group in self.hash_to_duplicates.values():
            if len(group) > 1:
                # pyrefly: ignore [implicit-any]
                region_group = []
                min_rank = math.inf

                for node in group:
                    # some nodes aren't in the topo ranking?
                    if node in topological_ranking:
                        min_rank = min(min_rank, topological_ranking[node])
                        region_group.append([node])

                if len(region_group) > 1:
                    region_groups_with_rank.append((region_group, min_rank))

        region_groups_with_rank.sort(key=lambda rg: -rg[1])
        region_groups = [rg for rg, _ in region_groups_with_rank]

        # We start from regions later in the graph and expand them earlier
        # as a result, we will create the largest regions first and they won't
        # overlap.
        seen_nodes: set[Node] = set()
        for region_group in region_groups:
            fully_expand_region_group(
                region_group,
                seen_nodes,
                node_to_recursive_ancestors,
                self._is_identical,
            )
            # sort topologically
            # we need to handle edge cases where some nodes have no dependencies
            # so first we map each node to its ranking,
            ref_region = region_group[0]
            index_to_rank = {
                index: topological_ranking[n] for index, n in enumerate(ref_region)
            }
            _sort_with_ref_region(index_to_rank, region_group)

        return [
            region_group for region_group in region_groups if len(region_group[0]) > 1
        ]