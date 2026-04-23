async def traced_build_vertex(self, vertex_id: str, *args, **kwargs):
        """Wrapped build_vertex that records execution."""
        self.trace.record_vertex_execution(vertex_id)

        # Capture state BEFORE building
        before_run_manager = None
        before_queue = None

        if hasattr(self.graph, "run_manager"):
            before_run_manager = self.graph.run_manager.to_dict()
            self.trace.record_run_manager_snapshot(before_run_manager)

        if hasattr(self.graph, "_run_queue"):
            before_queue = list(self.graph._run_queue)
            self.trace.record_run_queue_snapshot(before_queue)

        # Call original method
        result = await self.original_build_vertex(vertex_id, *args, **kwargs)

        # Record vertex result
        if result and hasattr(result, "result"):
            self.trace.vertex_results[vertex_id] = result.result

        # Capture loop state if this is a loop
        if result and hasattr(result, "vertex"):
            self._capture_loop_state(vertex_id, result.vertex)

        # Capture state AFTER building and compute deltas
        delta = {"vertex_id": vertex_id}

        if hasattr(self.graph, "run_manager"):
            after_run_manager = self.graph.run_manager.to_dict()
            self.trace.record_run_manager_snapshot(after_run_manager)

            if before_run_manager:
                run_manager_delta = self._compute_run_manager_delta(before_run_manager, after_run_manager)
                if run_manager_delta:
                    delta["run_manager"] = run_manager_delta

        if hasattr(self.graph, "_run_queue"):
            after_queue = list(self.graph._run_queue)
            self.trace.record_run_queue_snapshot(after_queue)

            if before_queue is not None:
                queue_delta = self._compute_queue_delta(before_queue, after_queue)
                if queue_delta["added"] or queue_delta["removed"]:
                    delta["queue"] = queue_delta

        # Record delta if anything changed
        if len(delta) > 2:  # More than just vertex_id and step
            self.trace.record_state_delta(vertex_id, delta)

        return result