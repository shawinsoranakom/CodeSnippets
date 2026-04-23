def _merge_overlapping_fusions(self) -> None:
        """
        Merge fusion groups that share nodes.

        FxNetAccFusionsFinder can produce overlapping fusion groups when a
        node is absorbed into multiple groups during expansion. When
        update_deps_for_fusions() later propagates deps, shared nodes act
        as bridges between groups, creating bidirectional dependency cycles
        that crash the splitter with "Subgraph can't be empty".

        This method detects overlapping groups via union-find and merges
        them into single groups before dep propagation.
        """
        if os.environ.get("_SPLITTER_MERGE_OVERLAPPING_FUSIONS", "0") != "1":
            return

        if not self.fusions:
            return

        # Collect unique groups by identity.
        unique_groups: dict[int, NodeSet] = {}
        for group in self.fusions.values():
            unique_groups[id(group)] = group

        if len(unique_groups) <= 1:
            return

        # Map each node to all group IDs it belongs to.
        node_to_gids: dict[torch.fx.Node, list[int]] = defaultdict(list)
        for gid, group in unique_groups.items():
            for node in group:
                node_to_gids[node].append(gid)

        # Union-find: merge groups that share nodes.
        parent: dict[int, int] = {gid: gid for gid in unique_groups}

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        needs_merge = False
        for gids in node_to_gids.values():
            if len(gids) > 1:
                root = find(gids[0])
                for i in range(1, len(gids)):
                    other = find(gids[i])
                    if other != root:
                        parent[other] = root
                        needs_merge = True

        if not needs_merge:
            return

        # Build merged groups.
        merged: dict[int, NodeSet] = defaultdict(set)
        for gid, group in unique_groups.items():
            merged[find(gid)].update(group)

        # Rebuild self.fusions so every node points to its merged group.
        for merged_group in merged.values():
            for node in merged_group:
                self.fusions[node] = merged_group