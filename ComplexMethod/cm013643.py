def match(self, graph: Graph, node_name_match: str = "") -> list[InternalMatch]:
        """
        Returns:
            The matched subgraphs.
            The returned subgraph would be fully self-contained, meaning the nodes (except placeholder
            and nodes returned by output) can only be consumed by nodes within the matched subgraph.

        Subgraph pattern matcher is implemented with the backtracking style in the following steps:

        1. We first identify all the anchor nodes in the pattern graph. The anchor nodes
        are the "sinks" (nodes with no user other than the output node) of the pattern graph.
        One pattern graph could have multiple anchors if it has multiple return values.

        2. In the target graph, we identify the potential candidate nodes that can be matched
        with each anchor. These anchor-candidate pairs are the starting points for
        pairwise per-node matching.

        3. For each anchor-candidate pair, we simultaneously traverse backwards (DFS) in both
        pattern and target graphs. For every pattern nodes along traversal path, we compare it
        against the target nodes. In case any comparison failed, the match for this anchor-candidate
        pair fails. A match is found when DFS completes traversing the graph. See `self._match_nodes`
        for more details.

        4. In the case of multiple anchors, every anchor will need to find a match using step 3.
        In addition, the matches found between anchors need to have a common intersection node
        in order for the match to be valid. This is implemented with backtracking. See `backtracking`
        for more details.

        Notice: graph traversal must be done in the reverser order because a tensor can have multiple
        consumers, but can only have a single producer. Only with reverser order, we can we jointly
        traverse the pattern and target graph in a deterministic path.

        Warning: In theory, this backtracking algorithm have an **exponential** time complexity. However,
        in practice, it's unlikely to blow up.

        """
        from torch.fx.passes.utils.fuser_utils import validate_partition

        # find candidate nodes to match with pattern anchors
        match_candidates: dict[Node, list[Node]] = defaultdict(list)
        for pattern_anchor in self.pattern_anchors:
            for node in graph.nodes:
                if self._nodes_are_equal(pattern_anchor, node, node_name_match):
                    match_candidates[pattern_anchor].append(node)
        match_candidates_list = list(match_candidates.items())

        logger.info("Initial match_candidates_list: %s\n", match_candidates_list)

        matches: list[InternalMatch] = []

        def backtracking(anchor_index: int, match: InternalMatch) -> None:
            if anchor_index == len(match_candidates_list):
                match.placeholder_nodes = [
                    match.nodes_map[pn] for pn in self.pattern_placeholder_nodes
                ]
                match.returning_nodes = [
                    match.nodes_map[pn] for pn in self.pattern_returning_nodes
                ]
                matches.append(match)

                logger.info("Found a match: %s\n", match)
                return

            pattern_anchor, candidate_nodes = match_candidates_list[anchor_index]
            saved_match = copy.copy(match)

            for node in candidate_nodes:
                logger.info("Trying to match anchor %s to %s", pattern_anchor, node)

                match_found = self._match_nodes(
                    pattern_anchor, node, match, node_name_match
                )
                if match_found:
                    # match next anchor
                    backtracking(anchor_index + 1, match)
                else:
                    logger.info(
                        "Failed to match anchor %s to %s\n", pattern_anchor, node
                    )

                # revert to saved_match before matching with current anchor
                match = copy.copy(saved_match)

        match = InternalMatch(anchors=self.pattern_anchors)
        if match_candidates_list:
            backtracking(0, match)

        # filter out the matches where the subgraph is not fully_contained
        before = len(matches)
        matches = [match for match in matches if self._is_contained(match.nodes_map)]
        after = len(matches)
        if before != after:
            logger.info(
                "Filtered out %s matches because they are not fully contained",
                before - after,
            )

        # filter out the matches that form a cycle if the subgraph is fused
        valid_matches: list[InternalMatch] = []
        for match in matches:
            matched_compute_nodes = [
                gn
                for pn, gn in match.nodes_map.items()
                if pn.op not in {"placeholder", "output"}
            ]
            if validate_partition(matched_compute_nodes):
                valid_matches.append(match)
        if len(valid_matches) != len(matches):
            logger.info(
                "Filtered out %s matches because \
                          matched subgraph would form a cycle if fused",
                len(matches) - len(valid_matches),
            )

        if self.remove_overlapping_matches:
            before = len(valid_matches)
            matches = self._remove_overlapping_matches(valid_matches)
            after = len(matches)
            if before != after:
                logger.info(
                    "Filtered out %s matches because matched subgraphs are overlapping",
                    before - after,
                )

        logger.info("Matches returned: %s", matches)

        return matches