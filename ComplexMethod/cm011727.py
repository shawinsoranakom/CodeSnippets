def get_possible_fusions(
        self,
        nodes: list[BaseSchedulerNode],
        is_reorder_round: bool,
    ) -> list[tuple[BaseSchedulerNode, BaseSchedulerNode]]:
        """
        Helper to find all legal fusion opportunities, sorted by self.score_fusion()
        """
        possible_fusions = []
        seen = OrderedSet[tuple[BaseSchedulerNode, BaseSchedulerNode]]()

        def check_all_pairs(nodes: list[BaseSchedulerNode]) -> None:
            for node1_index, node1 in enumerate(nodes):
                for node2 in nodes[
                    node1_index + 1 : node1_index
                    + 1
                    + config.max_fusion_buffer_group_pairwise_attempts
                ]:
                    key = (node1, node2)
                    if key in seen:
                        continue
                    seen.add(key)

                    if self.can_fuse(node1, node2, is_reorder_round):
                        possible_fusions.append(key)
                    elif (node2.is_template() or node2.is_foreach()) and self.can_fuse(
                        node2, node1, is_reorder_round
                    ):
                        # foreach fusions and epilogue fusions are order dependent
                        possible_fusions.append((node2, node1))

        buffer_names_grouping = collections.defaultdict(list)
        for node in nodes:
            if self.unfusable_node(node):
                continue
            for buf in node.used_buffer_names():
                buffer_names_grouping[buf].append(node)
        for node_grouping in buffer_names_grouping.values():
            check_all_pairs(node_grouping)

        if config.aggressive_fusion:
            group_grouping = collections.defaultdict(list)
            for node in nodes:
                group = getattr(node, "group", None)
                if group:
                    group_grouping[group].append(node)
            for node_grouping in group_grouping.values():
                check_all_pairs(node_grouping)

        possible_fusions = self.get_possible_fusions_with_highest_priority(
            possible_fusions
        )
        possible_fusions.sort(key=self.score_fusion_key, reverse=True)
        fusion_log.debug("found %d possible fusions", len(possible_fusions))
        return possible_fusions