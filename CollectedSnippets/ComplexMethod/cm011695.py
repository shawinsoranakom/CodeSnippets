def can_fuse(cls, node1: BaseSchedulerNode, node2: BaseSchedulerNode) -> bool:
        """
        Check whether we can fuse two reductions with mix loop orders.
        """
        if not config.triton.mix_order_reduction:
            return False

        # TODO: Mix order reduction is not supported with cpp_wrapper yet
        if V.graph.cpp_wrapper:
            return False

        if not node1.is_gpu() or not node2.is_gpu():
            return False
        device_type = node1.get_device().type  # type: ignore[union-attr]
        if (
            device_type not in ("cuda", "xpu")
            or get_current_backend(device_type) != "triton"
        ):
            return False
        if not node1.is_reduction() or not node2.is_reduction():
            return False

        if (node1.ancestors & node2.get_operation_names()) or (
            node2.ancestors & node1.get_operation_names()
        ):
            # the two reductions have no producer/consumer relationship
            return False

        # check for mix reduction orders
        if not cls.has_mix_reduction_orders(node1, node2):
            return False

        # check common buffer accesses
        common_reads = MixOrderReduction.get_common_read(node1, node2)
        if len(common_reads) == 0:
            return False

        if cls.is_contiguous_node(node1):
            contiguous_node, other_node = node1, node2
        elif cls.is_contiguous_node(node2):
            contiguous_node, other_node = node2, node1
        else:
            return False

        g1 = cls.get_numel_rnumel(contiguous_node)
        nrow, ncol = g1

        # in non strict mode, we will skip the non-critical checks
        if not config.triton.mix_order_reduction_non_strict_mode:
            # the fused version has worse perf than non-fused version for
            # small workload. When a workload is small enough, data can be
            # fully cached by L2
            size_thres = 5 * 2**20

            # Call evaluate_expr rather than statically_known_geq since nrow can
            # have dynamic shape in real models.
            # Don't use hint directly since hint can be non-representative.
            if not V.graph.sizevars.guard_or_true(sympy.Ge(nrow * ncol, size_thres)):
                return False

            # We require more more row than columns since
            # 1, we prefer doing persistent reduction for each row
            # 2, we will split the reduction across the rows
            if not V.graph.sizevars.guard_or_true(sympy.Ge(nrow, ncol * 2)):
                return False

            # When nrow is small, ncol should also be small (due to the check
            # above). Thus the entire tensor should be well cached in L2.
            # Mix order reduction is less beneficial.
            if not V.graph.sizevars.guard_or_true(sympy.Ge(nrow, 4096)):
                return False

        # Make sure a persistent reduction will be generated
        if any(
            subnode.node.data.reduction_hint  # type: ignore[union-attr]
            not in (
                ReductionHint.INNER,
                ReductionHint.DEFAULT,
            )
            for subnode in contiguous_node.get_nodes()
            if subnode.is_reduction()
        ):
            return False

        # rnumel so large that we will not generated persistent reduction
        # We don't see real use cases with dynamic ncol. But if we do,
        # we should call evaluete_expr here which adds guards.
        if not V.graph.sizevars.statically_known_leq(ncol, 1024 * 16):
            return False

        if MixOrderReduction.is_split_reduction(contiguous_node):
            return False

        # Other reduction types like max/min is not supported yet.
        # There are no real use case as well.
        out = all(
            subnode.node.get_reduction_type()  # type: ignore[union-attr]
            in {
                "sum",
                "prod",
            }
            for subnode in other_node.get_nodes()
            if subnode.is_reduction()
        )
        return out