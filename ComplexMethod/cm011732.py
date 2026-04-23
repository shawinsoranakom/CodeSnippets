def _try_reorder_loops_for_candidates(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
    ) -> int:
        """
        Find common buffers with matching normalized stride order but different
        loop orders, and try to reorder loops to align them.
        """
        common_buffer_names = (
            node1.read_writes.buffer_names() & node2.read_writes.buffer_names()
        )
        node1_reads = {dep.name: dep for dep in node1.read_writes.reads}
        node1_writes = {dep.name: dep for dep in node1.read_writes.writes}
        node2_reads = {dep.name: dep for dep in node2.read_writes.reads}
        node2_writes = {dep.name: dep for dep in node2.read_writes.writes}

        candidates = []
        for buffer_name in common_buffer_names:
            lhs_dep = node1_writes.get(buffer_name) or node1_reads[buffer_name]
            rhs_dep = node2_writes.get(buffer_name) or node2_reads[buffer_name]

            is_write_read = (
                buffer_name in node1_writes and buffer_name in node2_reads
            ) or (buffer_name in node2_writes and buffer_name in node1_reads)

            if (
                lhs_dep.normalize_with_stride_order()
                == rhs_dep.normalize_with_stride_order()
            ):
                candidates.append(
                    (
                        is_write_read,
                        V.graph.sizevars.optimization_hint(
                            lhs_dep.get_numel(), fallback=0
                        ),
                        lhs_dep,
                        rhs_dep,
                    )
                )
            elif is_write_read:
                # A write→read dep failed normalize_with_stride_order.
                # This could be a dimension order issue (reordering can
                # fix it) or a factorization issue (only reindexing can).
                # Distinguish by checking if the write dep's sizes are
                # a subset of the read dep's — if so, reordering the
                # read's loops could align them.
                w = node1_writes.get(buffer_name) or node2_writes.get(buffer_name)
                r = node2_reads.get(buffer_name) or node1_reads.get(buffer_name)
                if isinstance(w, MemoryDep) and isinstance(r, MemoryDep):
                    sv = V.graph.sizevars
                    w_sizes = w.normalize().size
                    r_sizes = r.normalize().size
                    if not all(
                        any(sv.statically_known_equals(ws, rs) for rs in r_sizes)
                        for ws in w_sizes
                    ):
                        return -1

        if len(candidates) == 0:
            return -1

        # Prefer write→read deps over shared reads. Among same
        # priority, pick the largest buffer.
        _is_wr, _numel, lhs_dep, rhs_dep = max(
            candidates, key=operator.itemgetter(0, 1)
        )

        if not isinstance(lhs_dep, MemoryDep) or not isinstance(rhs_dep, MemoryDep):
            return -1

        if lhs_dep.num_vars != rhs_dep.num_vars:
            # this can happen due to we don't merge loops.
            # We can not do loop reordering in this case right now
            # Simply returning true if the two Deps are the same after
            # normalization (merging loops)
            if lhs_dep.normalize() == rhs_dep.normalize():
                return self.dep_size_hint(lhs_dep)
            return -1

        reordered = False
        # Only reorder loops for pointwise for now
        if not node1.is_reduction():
            reordered = node1.reorder_loops_by_dep_pair(lhs_dep, rhs_dep)
        elif not node2.is_reduction():
            reordered = node2.reorder_loops_by_dep_pair(rhs_dep, lhs_dep)
        else:
            loop_ordering_log.debug(
                "Don't reorder loops since both nodes are reductions: %s v.s. %s",
                node1.get_name(),
                node2.get_name(),
            )

        return self.score_fusion_memory(node1, node2) if reordered else -1