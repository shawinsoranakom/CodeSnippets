async def test_sensitive_fields_filtered_non_sensitive_shown():
    """Duplicate blocks with sensitive AND non-sensitive defaults.

    Sensitive fields (credentials, api_key, token, etc.) must be filtered
    from descriptions, while non-sensitive defaults must still appear.
    """
    block = MatchTextPatternBlock()
    node_a = _make_mock_node(
        block,
        "node_a",
        input_default={
            "match": "important",
            "token": "tok-secret-123",
            "secret": "my_secret_value",
            "case_sensitive": True,
        },
    )
    node_b = _make_mock_node(
        block,
        "node_b",
        input_default={
            "match": "other",
            "auth": "bearer xyz",
            "access_token": "at-456",
        },
    )

    link_a = _make_mock_link("tools_^_a_~_text", "text", "node_a", "orch")
    link_b = _make_mock_link("tools_^_b_~_text", "text", "node_b", "orch")

    mock_db = AsyncMock()
    mock_db.get_connected_output_nodes.return_value = [
        (link_a, node_a),
        (link_b, node_b),
    ]

    with patch(
        "backend.blocks.orchestrator.get_database_manager_async_client",
        return_value=mock_db,
    ):
        tools = await OrchestratorBlock._create_tool_node_signatures("orch")

    for tool in tools:
        desc = tool["function"].get("description", "")
        # Sensitive values must NOT appear
        assert "tok-secret-123" not in desc
        assert "my_secret_value" not in desc
        assert "bearer xyz" not in desc
        assert "at-456" not in desc
        assert "token=" not in desc
        assert "secret=" not in desc
        assert "auth=" not in desc
        assert "access_token=" not in desc

    # Non-sensitive defaults SHOULD appear in the descriptions
    all_descs = " ".join(t["function"].get("description", "") for t in tools)
    assert "match=" in all_descs
    assert '"important"' in all_descs or '"other"' in all_descs