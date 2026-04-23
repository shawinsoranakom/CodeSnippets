async def arun(
        self,
        inputs: list[dict[str, str]],
        *,
        inputs_components: list[list[str]] | None = None,
        types: list[InputType | None] | None = None,
        outputs: list[str] | None = None,
        session_id: str | None = None,
        stream: bool = False,
        fallback_to_env_vars: bool = False,
        event_manager: EventManager | None = None,
    ) -> list[RunOutputs]:
        """Runs the graph with the given inputs.

        Args:
            inputs (list[Dict[str, str]]): The input values for the graph.
            inputs_components (Optional[list[list[str]]], optional): Components to run for the inputs. Defaults to None.
            types (Optional[list[Optional[InputType]]], optional): The types of the inputs. Defaults to None.
            outputs (Optional[list[str]], optional): The outputs to retrieve from the graph. Defaults to None.
            session_id (Optional[str], optional): The session ID for the graph. Defaults to None.
            stream (bool, optional): Whether to stream the results or not. Defaults to False.
            fallback_to_env_vars (bool, optional): Whether to fallback to environment variables. Defaults to False.
            event_manager (EventManager | None): The event manager for the graph.

        Returns:
            List[RunOutputs]: The outputs of the graph.
        """
        # inputs is {"message": "Hello, world!"}
        # we need to go through self.inputs and update the self.raw_params
        # of the vertices that are inputs
        # if the value is a list, we need to run multiple times
        vertex_outputs = []
        if not isinstance(inputs, list):
            inputs = [inputs]
        elif not inputs:
            inputs = [{}]
        # Length of all should be the as inputs length
        # just add empty lists to complete the length
        if inputs_components is None:
            inputs_components = []
        for _ in range(len(inputs) - len(inputs_components)):
            inputs_components.append([])
        if types is None:
            types = []
        if session_id:
            self.session_id = session_id
        for _ in range(len(inputs) - len(types)):
            types.append("chat")  # default to chat
        for run_inputs, components, input_type in zip(inputs, inputs_components, types, strict=True):
            run_outputs = await self._run(
                inputs=run_inputs,
                input_components=components,
                input_type=input_type,
                outputs=outputs or [],
                stream=stream,
                session_id=session_id or "",
                fallback_to_env_vars=fallback_to_env_vars,
                event_manager=event_manager,
            )
            run_output_object = RunOutputs(inputs=run_inputs, outputs=run_outputs)
            await logger.adebug(f"Run outputs: {run_output_object}")
            vertex_outputs.append(run_output_object)
        return vertex_outputs