async def test_build_setup_requirements_from_credential_validation_error(
    setup_firecrawl_test_data,
):
    """When the scheduler raises a credential-flavoured GraphValidationError,
    the helper should rebuild the inline setup card from the graph schema."""
    graph = setup_firecrawl_test_data["graph"]
    tool = RunAgentTool()

    # Construct an error in the same shape the executor produces.
    error = GraphValidationError(
        message="Graph is invalid",
        node_errors={"some-node-id": {"credentials": "These credentials are required"}},
    )

    # Race path: all credential fields shown as missing.
    response = tool._build_setup_requirements_from_validation_error(
        graph=graph,
        error=error,
        session_id="test-session",
    )

    assert isinstance(response, SetupRequirementsResponse)
    assert response.graph_id == graph.id
    assert response.graph_version == graph.version
    assert response.setup_info.user_readiness.has_all_credentials is False
    assert response.setup_info.user_readiness.ready_to_run is False
    # The firecrawl fixture defines exactly one credential field (firecrawl
    # API key).  Pin the count so fixture drift is caught immediately.
    missing_credentials = response.setup_info.user_readiness.missing_credentials
    assert len(missing_credentials) == 1, (
        f"Expected exactly 1 credential from the firecrawl fixture, "
        f"got {len(missing_credentials)}: {list(missing_credentials.keys())}"
    )
    assert "credentials" in response.message.lower()
    # Message must be action-neutral: this helper is shared by the run
    # path and the schedule path, so hardcoding "scheduling again" would
    # mislead users on the run path.
    assert "scheduling again" not in response.message.lower()