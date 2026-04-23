async def generate_activity_status_for_execution(
    graph_exec_id: str,
    graph_id: str,
    graph_version: int,
    execution_stats: GraphExecutionStats,
    db_client: "DatabaseManagerAsyncClient",
    user_id: str,
    execution_status: ExecutionStatus | None = None,
    model_name: str = "gpt-4o-mini",
    skip_feature_flag: bool = False,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    user_prompt: str = DEFAULT_USER_PROMPT,
    skip_existing: bool = True,
) -> ActivityStatusResponse | None:
    """
    Generate an AI-based activity status summary and correctness assessment for a graph execution.

    This function handles all the data collection and AI generation logic,
    keeping the manager integration simple.

    Args:
        graph_exec_id: The graph execution ID
        graph_id: The graph ID
        graph_version: The graph version
        execution_stats: Execution statistics
        db_client: Database client for fetching data
        user_id: User ID for LaunchDarkly feature flag evaluation
        execution_status: The overall execution status (COMPLETED, FAILED, TERMINATED)
        model_name: AI model to use for generation (default: gpt-4o-mini)
        skip_feature_flag: Whether to skip LaunchDarkly feature flag check
        system_prompt: Custom system prompt template (default: DEFAULT_SYSTEM_PROMPT)
        user_prompt: Custom user prompt template with placeholders (default: DEFAULT_USER_PROMPT)
        skip_existing: Whether to skip if activity_status and correctness_score already exist

    Returns:
        AI-generated activity status response with activity_status and correctness_status,
        or None if feature is disabled or skipped
    """
    # Check LaunchDarkly feature flag for AI activity status generation with full context support
    if not skip_feature_flag and not await is_feature_enabled(
        Flag.AI_ACTIVITY_STATUS, user_id
    ):
        logger.debug("AI activity status generation is disabled via LaunchDarkly")
        return None

    # Check if we should skip existing data (for admin regeneration option)
    if (
        skip_existing
        and execution_stats.activity_status
        and execution_stats.correctness_score is not None
    ):
        logger.debug(
            f"Skipping activity status generation for {graph_exec_id}: already exists"
        )
        return {
            "activity_status": execution_stats.activity_status,
            "correctness_score": execution_stats.correctness_score,
        }

    # Check if we have OpenAI API key
    try:
        settings = Settings()
        if not settings.secrets.openai_internal_api_key:
            logger.debug(
                "OpenAI API key not configured, skipping activity status generation"
            )
            return None

        # Get all node executions for this graph execution
        node_executions = await db_client.get_node_executions(
            graph_exec_id, include_exec_data=True
        )

        # Get graph metadata and full graph structure for name, description, and links
        graph_metadata = await db_client.get_graph_metadata(graph_id, graph_version)
        graph = await db_client.get_graph(
            graph_id=graph_id,
            version=graph_version,
            user_id=user_id,
            skip_access_check=True,
        )

        graph_name = graph_metadata.name if graph_metadata else f"Graph {graph_id}"
        graph_description = graph_metadata.description if graph_metadata else ""
        graph_links = graph.links if graph else []

        # Build execution data summary
        execution_data = _build_execution_summary(
            node_executions,
            execution_stats,
            graph_name,
            graph_description,
            graph_links,
            execution_status,
        )

        # Prepare execution data as JSON for template substitution
        execution_data_json = json.dumps(execution_data, indent=2)

        # Perform template substitution for user prompt
        user_prompt_content = user_prompt.replace("{{GRAPH_NAME}}", graph_name).replace(
            "{{EXECUTION_DATA}}", execution_data_json
        )

        # Prepare prompt for AI with structured output requirements
        prompt = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt_content,
            },
        ]

        # Log the prompt for debugging purposes
        logger.debug(
            f"Sending prompt to LLM for graph execution {graph_exec_id}: {json.dumps(prompt, indent=2)}"
        )

        # Create credentials for LLM call
        credentials = APIKeyCredentials(
            id="openai",
            provider="openai",
            api_key=SecretStr(settings.secrets.openai_internal_api_key),
            title="System OpenAI",
        )

        # Define expected response format
        expected_format = {
            "activity_status": "A user-friendly 1-3 sentence summary of what was accomplished",
            "correctness_score": "Float score from 0.0 to 1.0 indicating how well the execution achieved its intended purpose",
        }

        # Use existing AIStructuredResponseGeneratorBlock for structured LLM call
        structured_block = AIStructuredResponseGeneratorBlock()

        # Convert credentials to the format expected by AIStructuredResponseGeneratorBlock
        credentials_input = {
            "provider": credentials.provider,
            "id": credentials.id,
            "type": credentials.type,
            "title": credentials.title,
        }

        structured_input = AIStructuredResponseGeneratorBlock.Input(
            prompt=prompt[1]["content"],  # User prompt content
            sys_prompt=prompt[0]["content"],  # System prompt content
            expected_format=expected_format,
            model=LlmModel(model_name),
            credentials=credentials_input,  # type: ignore
            max_tokens=150,
            retry=3,
        )

        # Execute the structured LLM call
        async for output_name, output_data in structured_block.run(
            structured_input, credentials=credentials
        ):
            if output_name == "response":
                response = output_data
                break
        else:
            raise RuntimeError("Failed to get response from structured LLM call")

        # Create typed response with validation
        correctness_score = float(response["correctness_score"])
        # Clamp score to valid range
        correctness_score = max(0.0, min(1.0, correctness_score))

        activity_response: ActivityStatusResponse = {
            "activity_status": response["activity_status"],
            "correctness_score": correctness_score,
        }

        logger.debug(
            f"Generated activity status for {graph_exec_id}: {activity_response}"
        )

        return activity_response

    except Exception as e:
        logger.exception(
            f"Failed to generate activity status for execution {graph_exec_id}: {str(e)}"
        )
        return None