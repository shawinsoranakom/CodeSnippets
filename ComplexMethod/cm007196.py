async def build(
        self,
        user_id=None,
        inputs: dict[str, Any] | None = None,
        files: list[str] | None = None,
        requester: Vertex | None = None,
        event_manager: EventManager | None = None,
        **kwargs,
    ) -> Any:
        # Add lazy loading check at the beginning
        # Check if we need to fully load this component first
        from lfx.interface.components import ensure_component_loaded
        from lfx.services.deps import get_settings_service

        settings_service = get_settings_service()
        if settings_service and settings_service.settings.lazy_load_components:
            component_name = self.id.split("-")[0]
            await ensure_component_loaded(self.vertex_type, component_name, settings_service)

        # Continue with the original implementation
        async with self.lock:
            if self.state == VertexStates.INACTIVE:
                # If the vertex is inactive, return None
                self.build_inactive()
                return None

            # Loop components should always run, even when frozen,
            # because they need to iterate through their data
            is_loop_component = self.display_name == "Loop" or self.is_loop
            if self.frozen and self.built and not is_loop_component:
                return await self.get_requester_result(requester)
            if self.built and requester is not None:
                # This means that the vertex has already been built
                # and we are just getting the result for the requester
                return await self.get_requester_result(requester)
            self._reset()

            # Emit build_start event for webhook real-time feedback
            if self.graph and self.graph.flow_id:
                await emit_build_start_event(self.graph.flow_id, self.id)

            # inject session_id if it is not None
            if inputs is not None and "session" in inputs and inputs["session"] is not None and self.has_session_id:
                session_id_value = self.get_value_from_template_dict("session_id")
                if session_id_value == "":
                    self.update_raw_params({"session_id": inputs["session"]}, overwrite=True)
            if self._is_chat_input() and (inputs or files):
                chat_input = {}
                if (
                    inputs
                    and isinstance(inputs, dict)
                    and "input_value" in inputs
                    and inputs.get("input_value") is not None
                ):
                    chat_input.update({"input_value": inputs.get(INPUT_FIELD_NAME, "")})
                if files:
                    chat_input.update({"files": files})

                self.update_raw_params(chat_input, overwrite=True)

            # Run steps
            for step in self.steps:
                if step not in self.steps_ran:
                    await step(user_id=user_id, event_manager=event_manager, **kwargs)
                    self.steps_ran.append(step)

            self.finalize_build()

            # Log transaction after successful build
            flow_id = self.graph.flow_id
            if flow_id:
                # Extract outputs from outputs_logs for transaction logging
                outputs_dict = None
                if self.outputs_logs:
                    outputs_dict = {
                        k: v.model_dump() if hasattr(v, "model_dump") else v for k, v in self.outputs_logs.items()
                    }
                await self._log_transaction_async(
                    str(flow_id), source=self, target=None, status="success", outputs=outputs_dict
                )

        return await self.get_requester_result(requester)