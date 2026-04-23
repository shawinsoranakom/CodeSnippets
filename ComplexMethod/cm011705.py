def reorder_loops_by_dep_pair(
        self, self_dep: MemoryDep, other_dep: MemoryDep
    ) -> bool:
        """
        Return true if a loop reordering is performed.
        """
        if self.is_template():
            # We can not really reorder loops for a triton template
            return False
        self_sizes = None
        for snode in self.snodes:
            if not isinstance(snode, SchedulerNode):
                return False
            if self_sizes is not None and tuple(self_sizes) != tuple(snode._sizes[0]):
                loop_ordering_log.debug(
                    "Can not reorder fused node due to different sizes"
                )
                return False
            self_sizes = snode._sizes[0]
        new_order = None

        assert self_sizes is not None
        if len(self_sizes) == self_dep.num_vars == other_dep.num_vars:
            new_order = self_dep.decide_loop_order_to_match(other_dep)

        if not new_order:
            loop_ordering_log.debug(
                "Dont reordering fused node %s because we can not decide the suitable loop order",
                self.get_name(),
            )
            return False
        # pyrefly: ignore [bad-assignment]
        metrics.num_loop_reordering += 1
        loop_ordering_log.debug(
            "Reorder loops for fused node %s with order %s", self.get_name(), new_order
        )
        for snode in self.snodes:
            assert isinstance(snode, SchedulerNode)
            snode.apply_new_loop_order(new_order)

        refresh_group_node_dependencies(self)
        return True