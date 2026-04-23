def score_fusion_memory(
        self,
        node1: BaseSchedulerNode,
        node2: BaseSchedulerNode,
        count_bytes: bool = True,
        return_is_mix_order_reduction: bool = False,
        allow_mix_order_reduction: bool = True,
    ) -> int | tuple[int, int, bool]:
        """
        The first term in our fusion score that estimates number of saved
        memory operations.

        This function scores fusion candidates based on shared memory access patterns.
        Higher scores indicate better fusion candidates.

        Scoring strategy:
        1. If nodes share exact memory deps (same buffer + same indexing), return
           the sum of shared dep sizes (original behavior).
        2. If no exact matches (score == 0), check for same-buffer reads with
           different indexing (e.g., split operations reading different slices).
           - Give bonus if nodes read from exactly the same set of buffers
           - Score based on overlap ratio: common_buffer_size / total_read_size
           - High overlap (>50%) suggests good cache locality benefit from fusion
        """

        def _construct_return_value(
            score, buffer_overlap_score, is_mix_order_reduction
        ):
            if return_is_mix_order_reduction:
                return (score, buffer_overlap_score, is_mix_order_reduction)
            return score + buffer_overlap_score

        if allow_mix_order_reduction and MixOrderReduction.can_fuse(node1, node2):
            # The fusion score for mix order reduction only count
            # numel so far. It's actually fine. This makes other fusions
            # sharing the same amount of numels go first; but make
            # fusions only share weight/bias go later.
            score = MixOrderReduction.get_fusion_score(node1, node2)
            return _construct_return_value(score, 0, True)

        # For UserDefinedTritonKernel, the write deps are StarDep that won't
        # match the epilogue's MemoryDep via set intersection.  For templates,
        # a view/reshape between the template output and epilogue can produce
        # different index expressions that don't match via set intersection.
        # Fall back to name-based matching so that the fusion score reflects
        # the actual shared buffers.
        if (
            (
                isinstance(node1.node, ir.UserDefinedTritonKernel)
                and node1.node.can_fuse_epilogue()
            )
            or node1.is_template()
            or node2.is_template()
        ):
            node1_deps = node1.read_writes.reads | node1.read_writes.writes
            node2_deps = node2.read_writes.reads | node2.read_writes.writes

            def _match(dep1: Dep, dep2: Dep):
                if dep1 == dep2:
                    return True
                if isinstance(dep1, (StarDep, MemoryDep)) and isinstance(
                    dep2, (StarDep, MemoryDep)
                ):
                    return dep1.name == dep2.name
                return False

            score = 0
            for node1_dep in node1_deps:
                for node2_dep in node2_deps:
                    if _match(node1_dep, node2_dep):
                        score += max(
                            self.dep_size_hint(node1_dep), self.dep_size_hint(node2_dep)
                        )

            return _construct_return_value(score, 0, False)

        node1_dep_len = len(node1.read_writes.reads) + len(node1.read_writes.writes)
        node2_dep_len = len(node2.read_writes.reads) + len(node2.read_writes.writes)

        # optimization: iter over smaller set
        if min(node1_dep_len, node2_dep_len) * 4 < max(node1_dep_len, node2_dep_len):
            if node1_dep_len > node2_dep_len:
                node1, node2 = node2, node1

            deps = [
                dep
                for dep in node1.read_writes.reads | node1.read_writes.writes
                if dep in node2.read_writes.reads or dep in node2.read_writes.writes
            ]

            return _construct_return_value(
                sum(self.dep_size_hint(dep, count_bytes) for dep in deps), 0, False
            )

        common_memory_deps = (node1.read_writes.reads | node1.read_writes.writes) & (
            node2.read_writes.reads | node2.read_writes.writes
        )

        score = sum(self.dep_size_hint(dep) for dep in common_memory_deps)

        # If no exact dep matches, check for same-buffer reads with different indexing.
        # This handles cases like split operations that read different slices of the
        # same buffer - they should fuse for cache locality benefits.
        buffer_overlap_score = 0
        if score == 0 and self._can_use_buffer_overlap_scoring(node1, node2):
            buffer_overlap_score = self._score_fusion_memory_by_buffer_overlap(
                node1, node2
            )

        return _construct_return_value(score, buffer_overlap_score, False)