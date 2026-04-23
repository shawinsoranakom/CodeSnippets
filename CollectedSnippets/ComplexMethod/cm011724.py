def _evaluate_pending_template_fusions(
        self,
        template_fusion_candidates: dict[BaseSchedulerNode, list[PendingFusion]],
        fused_nodes: OrderedSet[BaseSchedulerNode],
    ) -> None:
        """
        Evaluate pending template fusions for a set of fusion candidate nodes.
        The fusion candidate nodes are pointwise nodes as potential epilogue
        or prologue fusions
        """

        while template_fusion_candidates:
            template_futures: list[Future] = []
            future_to_pending_fusion: dict[
                Future, tuple[PendingFusion, BaseSchedulerNode]
            ] = {}
            fusions_to_remove: OrderedSet[BaseSchedulerNode] = OrderedSet()
            for candidate in template_fusion_candidates:
                assert (
                    candidate in template_fusion_candidates
                    and len(template_fusion_candidates[candidate]) >= 1
                )
                pending_fusion = template_fusion_candidates[candidate].pop(0)

                if len(template_fusion_candidates[candidate]) == 0:
                    fusions_to_remove.add(candidate)

                node1, node2 = pending_fusion.get_fusion_nodes()

                if node2 == candidate:
                    assert is_epilogue_fusion(node1, node2)
                    template_node = node1
                else:
                    assert node1 == candidate
                    assert is_prologue_fusion(node1, node2)
                    template_node = node2

                # template node fused with same class of pointwise (prologue/epilogue)
                # move onto next candidate as not fusible
                # TODO (PaulZhang12): Does not support fusions of templates with
                # multiple potential epilogues
                if self.get_fused_node(template_node) is not template_node:
                    continue

                if pending_fusion.future:
                    f = pending_fusion.future.future
                    assert f is not None
                    template_futures.append(f)
                    future_to_pending_fusion[f] = (pending_fusion, candidate)
                else:
                    # Non AsyncCompile path, perform fusion
                    if self.fuse_if_speedup(
                        node1, node2, pending_fusion.callable_fn, fused_nodes
                    ):
                        fusions_to_remove.add(candidate)

            # Evaluate fusion candidates as async_compile completes
            for f in as_completed(template_futures):
                pending_fusion, cand = future_to_pending_fusion[f]
                if self.fuse_if_speedup(
                    self.get_fused_node(pending_fusion.node1),
                    self.get_fused_node(pending_fusion.node2),
                    pending_fusion.callable_fn,
                    fused_nodes,
                ):
                    fusions_to_remove.add(cand)

            for f in fusions_to_remove:
                template_fusion_candidates.pop(f)