def generate_stream_ctx_switching(self, node: BaseSchedulerNode) -> None:
        """Generate stream entering and exiting to properly run node in a multi-stream scenario.

        Stream context switching is only generated if ``node``'s assigned stream is different from
        the previous node's stream. NopKernelSchedulerNodes have stream=None and inherit the
        enclosing stream context (or do nothing if no context is active yet).
        """
        assert node in self.node_to_stream
        stream = (
            None
            if isinstance(node, NopKernelSchedulerNode)
            else self.node_to_stream[node]
        )
        if self.current_stream_idx == stream:
            # Covers: same stream as current (no switch needed), and both None
            # (nop node before any stream context — nothing to do).
            return
        elif self.current_stream_idx is not None and stream is None:
            # Don't generate ctx switching. Memory planning code (e.g., delete buffers) on current
            # node goes to previous stream ctx.
            return
        elif self.current_stream_idx is None and stream is not None:
            # Enter new ctx, update current stream status.
            self.generate_stream_ctx_enter(node)
        else:
            # Switching from previous stream ctx to the new stream ctx.
            self.generate_stream_ctx_exit()
            self.generate_stream_ctx_enter(node)