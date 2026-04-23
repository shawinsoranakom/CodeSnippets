async def test_run_block_returns_details_when_no_input_provided():
    """When run_block is called without input_data, it should return BlockDetailsResponse."""
    session = make_session(user_id=_TEST_USER_ID)

    # Create a block with inputs
    http_block = make_mock_block_with_inputs(
        "http-block-id", "HTTP Request", "Send HTTP requests"
    )

    with patch(
        "backend.copilot.tools.helpers.get_block",
        return_value=http_block,
    ):
        # Mock credentials check to return no missing credentials
        with patch(
            "backend.copilot.tools.helpers.resolve_block_credentials",
            new_callable=AsyncMock,
            return_value=({}, []),  # (matched_credentials, missing_credentials)
        ):
            tool = RunBlockTool()
            response = await tool._execute(
                user_id=_TEST_USER_ID,
                session=session,
                block_id="http-block-id",
                input_data={},  # Empty input data
                dry_run=False,
            )

    # Should return BlockDetailsResponse showing the schema
    assert isinstance(response, BlockDetailsResponse)
    assert response.block.id == "http-block-id"
    assert response.block.name == "HTTP Request"
    assert response.block.description == "Send HTTP requests"
    assert "url" in response.block.inputs["properties"]
    assert "method" in response.block.inputs["properties"]
    assert "response" in response.block.outputs["properties"]
    assert response.user_authenticated is True