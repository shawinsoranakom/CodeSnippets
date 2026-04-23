async def _check_prerequisites(
        self,
        graph: GraphModel,
        user_id: str,
        params: "RunAgentInput",
        session_id: str,
    ) -> tuple[dict[str, CredentialsMetaInput], ToolResponseBase | None]:
        """Validate credentials and inputs before execution.

        Dry runs skip all prerequisite gates (credentials, input prompts).
        The dry_run flag is read from params.dry_run (which may be set by the
        LLM per-call, or forced to True when session.dry_run is True).

        Returns:
            (graph_credentials, error_response) — error_response is None when ready.
        """
        graph_credentials, missing_creds = await match_user_credentials_to_graph(
            user_id, graph
        )

        # --- Reject unknown input fields (always, even for dry runs) ---
        input_properties = graph.input_schema.get("properties", {})
        provided_inputs = set(params.inputs.keys())
        valid_fields = set(input_properties.keys())
        unrecognized_fields = provided_inputs - valid_fields
        if unrecognized_fields:
            return graph_credentials, InputValidationErrorResponse(
                message=(
                    f"Unknown input field(s) provided: {', '.join(sorted(unrecognized_fields))}. "
                    f"Agent was not executed. Please use the correct field names from the schema."
                ),
                session_id=session_id,
                unrecognized_fields=sorted(unrecognized_fields),
                inputs=graph.input_schema,
                graph_id=graph.id,
                graph_version=graph.version,
            )

        # Dry runs bypass remaining prerequisite gates (credentials, missing inputs)
        if params.dry_run:
            return graph_credentials, None

        # --- Credential gate ---
        if missing_creds:
            requirements_creds_dict = build_missing_credentials_from_graph(graph, None)
            missing_credentials_dict = build_missing_credentials_from_graph(
                graph, graph_credentials
            )
            return graph_credentials, SetupRequirementsResponse(
                message=self._build_inputs_message(graph, MSG_WHAT_VALUES_TO_USE),
                session_id=session_id,
                setup_info=SetupInfo(
                    agent_id=graph.id,
                    agent_name=graph.name,
                    user_readiness=UserReadiness(
                        has_all_credentials=False,
                        missing_credentials=missing_credentials_dict,
                        ready_to_run=False,
                    ),
                    requirements={
                        "credentials": list(requirements_creds_dict.values()),
                        "inputs": get_inputs_from_schema(graph.input_schema),
                        "execution_modes": self._get_execution_modes(graph),
                    },
                ),
                graph_id=graph.id,
                graph_version=graph.version,
            )

        # --- Input gates ---
        required_fields = set(graph.input_schema.get("required", []))

        # Prompt user when inputs exist but none were provided
        if input_properties and not provided_inputs and not params.use_defaults:
            credentials = extract_credentials_from_schema(
                graph.credentials_input_schema
            )
            return graph_credentials, AgentDetailsResponse(
                message=self._build_inputs_message(graph, MSG_ASK_USER_FOR_VALUES),
                session_id=session_id,
                agent=self._build_agent_details(graph, credentials),
                user_authenticated=True,
                graph_id=graph.id,
                graph_version=graph.version,
            )

        # Required inputs missing
        missing_inputs = required_fields - provided_inputs
        if missing_inputs and not params.use_defaults:
            credentials = extract_credentials_from_schema(
                graph.credentials_input_schema
            )
            return graph_credentials, AgentDetailsResponse(
                message=(
                    f"Agent '{graph.name}' is missing required inputs: "
                    f"{', '.join(missing_inputs)}. "
                    "Please provide these values to run the agent."
                ),
                session_id=session_id,
                agent=self._build_agent_details(graph, credentials),
                user_authenticated=True,
                graph_id=graph.id,
                graph_version=graph.version,
            )

        return graph_credentials, None