def _handle_pdl_before_access(
        self, wait_buffer, *dependencies, consider_reads=False
    ):
        if not self._enable_pdl_codegen():
            return
        current_node = V.kernel.current_node
        prev_node = (
            V.graph.scheduler.previous_node if V.graph.scheduler is not None else None
        )

        def matching_dep(dep):
            assert prev_node is not None
            prev_deps = prev_node.read_writes.writes
            if consider_reads:
                prev_deps = itertools.chain(prev_deps, prev_node.read_writes.reads)
            return any(
                dep == current_node.mutation_renames.get(w.name, w.name)
                for w in prev_deps
            )

        assert dependencies
        need_wait = prev_node is None or any(matching_dep(d) for d in dependencies)
        if not need_wait:
            return
        # hoist before the loop
        if self.inside_reduction and self.range_trees[-1].is_loop:
            wait_buffer = self.body

        wait_buffer.writeline(self.GDC_WAIT)