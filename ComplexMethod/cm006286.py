def end_trace(
        self,
        trace_id: str,
        trace_name: str,
        outputs: dict[str, Any] | None = None,
        error: Exception | None = None,
        logs: Sequence[Log | dict] = (),
    ) -> None:
        """Update SDK Step with outputs."""
        if not self._ready:
            return

        step = self.component_steps.get(trace_id)
        if not step:
            return

        # Set end time and latency (as int for API compatibility)
        step.end_time = time.time()
        if hasattr(step, "start_time") and step.start_time:
            step.latency = int((step.end_time - step.start_time) * 1000)  # ms as int

        # Update output
        if outputs:
            step.output = self._convert_to_openlayer_types(outputs)

        # Add error and logs to metadata
        if error:
            if not step.metadata:
                step.metadata = {}
            step.metadata["error"] = str(error)
        if logs:
            if not step.metadata:
                step.metadata = {}
            step.metadata["logs"] = [log if isinstance(log, dict) else log.model_dump() for log in logs]

        # Clear current step context
        # Use None as positional argument to avoid LookupError when ContextVar is not set
        current_step = self._openlayer_tracer._current_step.get(None)
        if current_step == step:
            self._openlayer_tracer._current_step.set(None)