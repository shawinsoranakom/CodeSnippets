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