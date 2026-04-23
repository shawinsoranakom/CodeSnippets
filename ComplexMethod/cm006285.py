def add_trace(
        self,
        trace_id: str,
        trace_name: str,
        trace_type: str,
        inputs: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        vertex: Vertex | None = None,
    ) -> None:
        """Create SDK Step object for component."""
        if not self._ready:
            return

        # Create trace on first component and set in SDK context
        if self.trace_obj is None:
            self.trace_obj = self._openlayer_traces.Trace()
            self._openlayer_tracer._current_trace.set(self.trace_obj)

        # Extract session/user from inputs and update SDK context
        if inputs and "session_id" in inputs and inputs["session_id"] != self.flow_id:
            self.session_id = inputs["session_id"]
            self._user_session_context.set_session_id(self.session_id)
        if inputs and "user_id" in inputs:
            self.user_id = inputs["user_id"]
            self._user_session_context.set_user_id(self.user_id)

        # Clean component name
        name = trace_name.removesuffix(f" ({trace_id})")

        # Map LangFlow trace_type to Openlayer StepType
        step_type = self._step_type_map.get(trace_type, self._openlayer_enums.StepType.USER_CALL)

        # Convert inputs and metadata
        converted_inputs = self._convert_to_openlayer_types(inputs) if inputs else {}
        converted_metadata = self._convert_to_openlayer_types(metadata) if metadata else {}

        # Create Step using SDK step_factory
        try:
            step = self._openlayer_steps.step_factory(
                step_type=step_type,
                name=name,
                inputs=converted_inputs,
                metadata=converted_metadata,
            )
            step.start_time = time.time()
        except Exception:  # noqa: BLE001
            return

        # Store step and set as current in SDK context
        self.component_steps[trace_id] = step

        # Set as current step so LangChain callbacks can nest under it
        self._openlayer_tracer._current_step.set(step)