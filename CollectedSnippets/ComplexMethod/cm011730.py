def shared_data_after_inverting_indexing(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> int:
        """
        Attempts to enable fusion between two nodes by inverting indexing patterns.

        This optimization targets cases where node1 has a contiguous write and
        node2 has a contiguous write but discontiguous read. By inverting the
        indexing in node2's read and write operations, we can make them compatible
        with node1 for potential fusion.

        Args:
            node1: First scheduler node (source)
            node2: Second scheduler node (target for inversion)

        Returns:
            int: Fusion score if successful, 0 if optimization not applicable
        """

        if not config.loop_index_inversion_in_fusion:
            return -1

        if any(n.is_cpu() for n in [node1, node2]):
            return -1

        # Check for shared buffers between nodes
        node1_buffer_names = node1.read_writes.buffer_names()
        node2_buffer_names = node2.read_writes.buffer_names()
        common_buffer_names = node1_buffer_names & node2_buffer_names

        if not common_buffer_names:
            return -1

        # only invert if node1 is single unmet dep
        node2_unmet_dependencies = OrderedSet(
            dep.name for dep in node2.unmet_dependencies
        )
        if node2_unmet_dependencies - node1_buffer_names:
            return -1

        if len(node2_unmet_dependencies) > 1:
            return -1

        # Currently only handle single read/write operations
        if len(node2.read_writes.reads) > 1 or len(node2.read_writes.writes) > 1:
            return -1

        node2_read = next(iter(node2.read_writes.reads))
        node2_write = next(iter(node2.read_writes.writes))

        if not isinstance(node2_read, MemoryDep) or not isinstance(
            node2_write, MemoryDep
        ):
            return -1

        node1_writes = {dep.name: dep for dep in node1.read_writes.writes}
        if node2_read.name not in node1_writes:
            return -1

        node1_write = node1_writes[node2_read.name]

        if not isinstance(node1_write, MemoryDep):
            return -1

        # We are checking for compatibility with the normalized node1 write
        # then modifying node2 reads/writes. since the node1 write will be just used
        # for compatibility, while node2 will be used in actual modification, just
        # normalize node1 not node2.
        node1_write = node1_write.normalize()

        if (
            node1_write.index != node2_write.index
            and node1_write.size != node2_write.size
        ):
            return -1

        if node2_read.size != node2_write.size or len(node2_read.var_names) != 1:
            return -1

        # Verify we have exactly two indexing expressions (one read, one write)
        if len(node2._body.indexing_exprs) != 2:  # type: ignore[attr-defined]
            return -1

        # No subblocks allowed for this optimization
        if node2._body.subblocks:  # type: ignore[attr-defined]
            return -1

        assert (
            "index0" in node2._body.indexing_exprs  # type: ignore[attr-defined]
            and "index1" in node2._body.indexing_exprs  # type: ignore[attr-defined]
        )

        # Extract and verify single read expression
        node2_read_exprs = OrderedSet(expr for expr in node2._body.get_read_exprs())  # type: ignore[attr-defined]
        if len(node2_read_exprs) != 1:
            return -1

        read_expr = next(iter(node2_read_exprs))

        # Determine which index is for reading vs writing
        if read_expr == node2._body.indexing_exprs["index0"]:  # type: ignore[attr-defined]
            read_expr_index = "index0"
            write_expr_index = "index1"
        else:
            assert read_expr == node2._body.indexing_exprs["index1"]  # type: ignore[attr-defined]
            read_expr_index = "index1"
            write_expr_index = "index0"

        from torch._inductor.invert_expr_analysis import generate_inverse_formula

        index_vars = node2._body.vars[0]  # type: ignore[attr-defined]
        if len(index_vars) != 1:
            return -1

        simplified_terms = []
        for term in sympy.Add.make_args(read_expr):
            simplified_terms.append(
                V.graph.sizevars.combine_modular_indexing_pairs(term)
            )
        simplified_read_expr = sum(simplified_terms)

        inverse_formula = generate_inverse_formula(simplified_read_expr, index_vars[0])

        # formula is not invertible
        if inverse_formula is None:
            return -1

        # === Apply Inversion ===

        # Swap the indexing expressions using the inverse formula
        node2._body.indexing_exprs[read_expr_index] = node2._body.indexing_exprs[  # type: ignore[attr-defined]
            write_expr_index
        ]
        node2._body.indexing_exprs[write_expr_index] = inverse_formula  # type: ignore[attr-defined]

        # Refresh dependencies and calculate fusion score
        node2.refresh_dependencies(True, False)  # type: ignore[attr-defined]
        score = self.score_fusion_memory(node1, node2)
        assert isinstance(score, int)

        fusion_log.info("Shared memory after inversion: %d", score)
        return score