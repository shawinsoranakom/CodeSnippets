def _try_fusion_pairs(
        self,
        possible_fusion_pairs: list[tuple[BaseSchedulerNode, BaseSchedulerNode]],
        pending_fusions: dict[BaseSchedulerNode, PendingFusion],
        template_fusion_nodes: dict[BaseSchedulerNode, list[PendingFusion]],
        fused_nodes: OrderedSet[BaseSchedulerNode],
        is_reorder_round: bool,
    ):
        def resolve_pending_fusions(
            node1: BaseSchedulerNode,
            node2: BaseSchedulerNode,
        ) -> None:
            while (
                self.get_fused_node(node1) in pending_fusions
                or self.get_fused_node(node2) in pending_fusions
            ):
                pending_fusion = pending_fusions.get(
                    self.get_fused_node(node1),
                    pending_fusions.get(self.get_fused_node(node2)),
                )
                assert pending_fusion is not None

                node_key1, node_key2 = pending_fusion.get_fusion_nodes()
                is_speedup = pending_fusion.callable_fn

                pending_fusions.pop(node_key1, None)
                pending_fusions.pop(node_key2, None)

                assert self.get_fused_node(node_key1) is node_key1
                assert self.get_fused_node(node_key2) is node_key2

                if not is_speedup() or self.will_fusion_create_cycle(node1, node2):
                    continue

                self.fuse_two_nodes(node_key1, node_key2, fused_nodes)

        for node1, node2 in possible_fusion_pairs:
            # if either node is in a pending fusion, resolve it.
            # since we iterate on potential fusions based on profitability
            # the first potential fusion should take precedence.
            resolve_pending_fusions(node1, node2)
            node1 = self.get_fused_node(node1)
            node2 = self.get_fused_node(node2)

            if (
                is_template_fusion(node1, node2)
                and (node1, node2) in self.seen_template_fusions
            ):
                continue

            if self.can_fuse(
                node1, node2, is_reorder_round
            ) and not self.will_fusion_create_cycle(node1, node2):
                fusion_res = self.speedup_by_fusion(node1, node2)
                if fusion_res.callable_fn is not None:
                    pending_fusion = PendingFusion(
                        callable_fn=fusion_res.callable_fn,
                        node1=node1,
                        node2=node2,
                        future=fusion_res.future,
                    )

                    if is_template_fusion(node1, node2):
                        assert (node1, node2) not in self.seen_template_fusions
                        self.seen_template_fusions.add((node1, node2))

                        template_pw_node = template_fusion_pw_node(node1, node2)
                        if template_pw_node not in template_fusion_nodes:
                            template_fusion_nodes[template_pw_node] = []
                        template_fusion_nodes[template_pw_node].append(pending_fusion)
                    else:
                        pending_fusions[node1] = pending_fusion
                        pending_fusions[node2] = pending_fusion

                    continue

                if not fusion_res.should_fuse:
                    continue

                self.fuse_two_nodes(node1, node2, fused_nodes)