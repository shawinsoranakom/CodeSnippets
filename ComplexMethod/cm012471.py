def plan(self, state: MemoryPlanningState) -> MemoryPlanningLine:
        if self.node.get_name() in V.graph.removed_buffers:
            return NullLine(self.wrapper)

        if self.comm_buffer:
            # Comm buffers use separate pool (comm-comm reuse only)
            key = comm_buffer_reuse_key(self.node)
            if config.allow_buffer_reuse and state.comm_buffer_contains(key):
                free_line = state.comm_buffer_pop(key)
                free_line.is_reused = True
                return ReuseLine(
                    self.wrapper, free_line.node, self.node, comm_buffer=True
                )
            return self

        # Regular buffer reuse
        # Stream is part of the key, so cross-stream reuse is naturally prevented.
        key = buffer_reuse_key(self.node)
        if config.allow_buffer_reuse and key in state:
            free_line = state.pop(key)
            size = V.graph.sizevars.optimization_hint(
                V.graph.get_allocation_storage_size(self.node), fallback=0
            ) * get_dtype_size(self.node.get_dtype())
            if self.should_reuse_buffer(free_line, size):
                free_line.is_reused = True
                self.wrapper.estimate_peak.update_peak_between(free_line, self)
                return ReuseLine(self.wrapper, free_line.node, self.node)
            else:
                state.push(key, free_line)
                return self

        if self.node.get_device_or_error().type == "cpu":
            static_shape = self.wrapper.static_shape_for_buffer_or_none(self.node)
            if static_shape is not None:
                state.total_allocated_buffer_size += int(
                    functools.reduce(operator.mul, static_shape, 1)
                )

        return self