async def test_clean_graph(server: SpinTestServer):
    """
    Test the stripped_for_export function that:
    1. Removes sensitive/secret fields from node inputs
    2. Removes webhook information
    3. Preserves non-sensitive data including input block values
    """
    # Create a graph with input blocks containing both sensitive and normal data
    graph = Graph(
        id="test_clean_graph",
        name="Test Clean Graph",
        description="Test graph cleaning",
        nodes=[
            Node(
                block_id=AgentInputBlock().id,
                input_default={
                    "_test_id": "input_node",
                    "name": "test_input",
                    "value": "test value",  # This should be preserved
                    "description": "Test input description",
                },
            ),
            Node(
                block_id=AgentInputBlock().id,
                input_default={
                    "_test_id": "input_node_secret",
                    "name": "secret_input",
                    "value": "another value",
                    "secret": True,  # This makes the input secret
                },
            ),
            Node(
                block_id=StoreValueBlock().id,
                input_default={
                    "_test_id": "node_with_secrets",
                    "input": "normal_value",
                    "control_test_input": "should be preserved",
                    "api_key": "secret_api_key_123",  # Should be filtered # pragma: allowlist secret # noqa
                    "password": "secret_password_456",  # Should be filtered # pragma: allowlist secret # noqa
                    "token": "secret_token_789",  # Should be filtered
                    "credentials": {  # Should be filtered
                        "id": "fake-github-credentials-id",
                        "provider": "github",
                        "type": "api_key",
                    },
                    "anthropic_credentials": {  # Should be filtered
                        "id": "fake-anthropic-credentials-id",
                        "provider": "anthropic",
                        "type": "api_key",
                    },
                },
            ),
        ],
        links=[],
    )

    # Create graph and get model
    create_graph = CreateGraph(graph=graph)
    created_graph = await server.agent_server.test_create_graph(
        create_graph, DEFAULT_USER_ID
    )

    # Clean the graph
    cleaned_graph = await server.agent_server.test_get_graph(
        created_graph.id, created_graph.version, DEFAULT_USER_ID, for_export=True
    )

    # Verify sensitive fields are removed but normal fields are preserved
    input_node = next(
        n for n in cleaned_graph.nodes if n.input_default["_test_id"] == "input_node"
    )

    # Non-sensitive fields should be preserved
    assert input_node.input_default["name"] == "test_input"
    assert input_node.input_default["value"] == "test value"  # Should be preserved now
    assert input_node.input_default["description"] == "Test input description"

    # Sensitive fields should be filtered out
    assert "api_key" not in input_node.input_default
    assert "password" not in input_node.input_default

    # Verify secret input node preserves non-sensitive fields but removes secret value
    secret_node = next(
        n
        for n in cleaned_graph.nodes
        if n.input_default["_test_id"] == "input_node_secret"
    )
    assert secret_node.input_default["name"] == "secret_input"
    assert "value" not in secret_node.input_default  # Secret default should be removed
    assert secret_node.input_default["secret"] is True

    # Verify sensitive fields are filtered from nodes with secrets
    secrets_node = next(
        n
        for n in cleaned_graph.nodes
        if n.input_default["_test_id"] == "node_with_secrets"
    )
    # Normal fields should be preserved
    assert secrets_node.input_default["input"] == "normal_value"
    assert secrets_node.input_default["control_test_input"] == "should be preserved"
    # Sensitive fields should be filtered out
    assert "api_key" not in secrets_node.input_default
    assert "password" not in secrets_node.input_default
    assert "token" not in secrets_node.input_default
    assert "credentials" not in secrets_node.input_default
    assert "anthropic_credentials" not in secrets_node.input_default

    # Verify webhook info is removed (if any nodes had it)
    for node in cleaned_graph.nodes:
        assert node.webhook_id is None