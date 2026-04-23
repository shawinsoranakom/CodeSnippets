def can_fuse(self, node1, node2):
        """
        Hook called by Scheduler to determine if the Triton backend
        can fuse node1 and node2.  These nodes might already be
        FusedSchedulerNodes.
        """
        if isinstance(node1, scheduler.ForeachKernelSchedulerNode) or isinstance(
            node2, scheduler.ForeachKernelSchedulerNode
        ):
            return scheduler.ForeachKernelSchedulerNode.can_fuse(node1, node2)

        _, (numel1, rnumel1) = node1.group
        _, (numel2, rnumel2) = node2.group
        why = WhyNoFuse(node1, node2)

        if node1.is_split_scan() and not node2.is_split_scan():
            if node2.is_reduction():
                why("Split scan cannot fuse with reductions")
        elif node2.is_split_scan() and not node1.is_split_scan():
            if node1.is_reduction():
                why("Split scan cannot fuse with reductions")

        if node1.is_reduction() and node2.is_reduction():
            reduction_can_fuse = numel1 == numel2 and rnumel1 == rnumel2
            if not reduction_can_fuse:
                from torch._inductor.scheduler import MixOrderReduction

                reduction_can_fuse = MixOrderReduction.can_fuse(node1, node2)

            if not reduction_can_fuse:
                why(
                    "numel/rnumel mismatch (reduce) (%s, %s), (%s, %s)",
                    numel1,
                    numel2,
                    rnumel1,
                    rnumel2,
                )

            if reduction_can_fuse and (
                node1.is_native_matmul() or node2.is_native_matmul()
            ):
                # Ensure node1 is always the native matmul side
                if not node1.is_native_matmul():
                    node1, node2 = node2, node1

                # 1. A native matmul node keeps its original loop order.
                #    For example: C[z,y,x] = torch.bmm(A[z,y,r], B[z,r,x]) keeps (z,y,x) order.
                #    (see simplify_and_reorder in ir.py)
                #
                # 2. Triton kernels with native matmul always tile loops as (z,y,x)
                #    (see get_tiling_and_scores in this file)
                #
                # 3. If a candidate node (node2) uses a different loop order (e.g., (z,x,y,r)),
                #    its tiling is incompatible with native matmul tiling (z,y,x,r).
                #    This means _split_iteration_ranges will fail, so these nodes should not be fused.
                tiling = self.select_tiling(node1.get_nodes(), numel1, rnumel1)
                if not all(
                    SIMDKernel.is_compatible(
                        tiling.values(), n2.get_ranges(), reduction_numel=rnumel1
                    )
                    for n2 in node2.get_nodes()
                ):
                    why("invalid loop order and tiling for native matmul")
                    return False

            return reduction_can_fuse

        if not node1.is_reduction() and not node2.is_reduction():
            if not (numel1 == numel2 and rnumel1 == rnumel2):
                if not node2.is_template():
                    why(
                        "numel/rnumel mismatch (non-reduce) (%s, %s), (%s, %s)",
                        numel1,
                        numel2,
                        rnumel1,
                        rnumel2,
                    )
                    return False
                else:
                    # prologue fusion input sizes differ from output group
                    # fuse so long as this node matches the group of existing prologue nodes
                    for node in node2.get_nodes():
                        # dont need to check epilogue nodes for prologue fusion, break after template
                        if node.is_template():
                            break
                        # we would have already restricted prologue from fusing if it had multiple
                        # uses, so it must be fusing into this node
                        if not node.used_buffer_names() & node1.get_buffer_names():
                            continue
                        _, (pro_numel, pro_rnumel) = node.group
                        if not (numel1 == pro_numel and rnumel1 == pro_rnumel):
                            why(
                                "numel/rnumel mismatch prologue mismatch (%s, %s), (%s, %s)",
                                numel1,
                                pro_numel,
                                rnumel1,
                                pro_rnumel,
                            )
                            return False

            for n in (node1, node2):
                if n.is_template():
                    return True

            # check for a bad combined tiling
            tiling1 = self.select_tiling(node1.get_nodes(), numel1, rnumel1)
            tiling2 = self.select_tiling(node2.get_nodes(), numel1, rnumel1)
            tiling3 = self.select_tiling(
                node1.get_nodes() + node2.get_nodes(), numel1, rnumel1
            )
            if config.triton.tiling_prevents_pointwise_fusion:
                cond = True
                if len(tiling1) > 2:
                    if len(tiling2) > 2:
                        cond = tiling1 == tiling2 == tiling3
                    else:
                        cond = tiling1 == tiling3
                elif len(tiling2) > 2:
                    cond = tiling2 == tiling3
                if not cond:
                    why(
                        "tiling mismatch (%s, %s, %s)",
                        tiling1,
                        tiling2,
                        tiling3,
                    )
                    return False

            return True

        if not node1.is_reduction() and node2.is_reduction():
            assert rnumel1 == 1 and rnumel2 != 1
            if numel1 == numel2 * rnumel2:
                if not all(
                    SIMDKernel.is_compatible((numel2, rnumel2), n.get_ranges())
                    for n in node1.get_nodes()
                ):
                    why("nodes numel/rnumel incompatibility")
                    return False
                if (
                    config.triton.tiling_prevents_reduction_fusion
                    and not node1.is_template()
                ):
                    is_reduction_tiling_valid = tuple(
                        self.select_tiling(node1.get_nodes(), numel1).values()
                    ) in (
                        (numel1, 1),
                        (numel2, rnumel2, 1),
                    )
                    if not is_reduction_tiling_valid:
                        why("invalid tiling for reduction")
                    return is_reduction_tiling_valid
                return True

            if numel1 != numel2:
                why("nodes numel incompatibility")
            return numel1 == numel2

        assert node1.is_reduction() and not node2.is_reduction()
        # swap args to hit the case above
        return self.can_fuse_horizontal(node2, node1)