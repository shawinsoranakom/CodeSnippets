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