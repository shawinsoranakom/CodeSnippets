async def _run(
        self,
        *,
        inputs: dict[str, str],
        input_components: list[str],
        input_type: InputType | None,
        outputs: list[str],
        stream: bool,
        session_id: str,
        fallback_to_env_vars: bool,
        event_manager: EventManager | None = None,
    ) -> list[ResultData | None]:
        """Runs the graph with the given inputs.

        Args:
            inputs (Dict[str, str]): The input values for the graph.
            input_components (list[str]): The components to run for the inputs.
            input_type: (Optional[InputType]): The input type.
            outputs (list[str]): The outputs to retrieve from the graph.
            stream (bool): Whether to stream the results or not.
            session_id (str): The session ID for the graph.
            fallback_to_env_vars (bool): Whether to fallback to environment variables.
            event_manager (EventManager | None): The event manager for the graph.

        Returns:
            List[Optional["ResultData"]]: The outputs of the graph.
        """
        if input_components and not isinstance(input_components, list):
            msg = f"Invalid components value: {input_components}. Expected list"
            raise ValueError(msg)
        if input_components is None:
            input_components = []

        if not isinstance(inputs.get(INPUT_FIELD_NAME, ""), str):
            msg = f"Invalid input value: {inputs.get(INPUT_FIELD_NAME)}. Expected string"
            raise TypeError(msg)
        if inputs:
            self._set_inputs(input_components, inputs, input_type)
        # Update all the vertices with the session_id
        for vertex_id in self.has_session_id_vertices:
            vertex = self.get_vertex(vertex_id)
            if vertex is None:
                msg = f"Vertex {vertex_id} not found"
                raise ValueError(msg)
            vertex.update_raw_params({"session_id": session_id})
        # Process the graph
        try:
            cache_service = get_chat_service()
            if cache_service and self.flow_id:
                await cache_service.set_cache(self.flow_id, self)
        except Exception:  # noqa: BLE001
            logger.exception("Error setting cache")

        try:
            # Prioritize the webhook component if it exists
            start_component_id = find_start_component_id(self._is_input_vertices)
            await self.process(
                start_component_id=start_component_id,
                fallback_to_env_vars=fallback_to_env_vars,
                event_manager=event_manager,
            )
            self.increment_run_count()
        except Exception as exc:
            self._end_all_traces_async(error=exc)
            msg = f"Error running graph: {exc}"
            raise ValueError(msg) from exc

        self._end_all_traces_async()
        # Get the outputs
        vertex_outputs = []
        for vertex in self.vertices:
            if not vertex.built:
                continue
            if vertex is None:
                msg = f"Vertex {vertex_id} not found"
                raise ValueError(msg)

            if not vertex.result and not stream and hasattr(vertex, "consume_async_generator"):
                await vertex.consume_async_generator()
            if (not outputs and vertex.is_output) or (vertex.display_name in outputs or vertex.id in outputs):
                vertex_outputs.append(vertex.result)

        return vertex_outputs