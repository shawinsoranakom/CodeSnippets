async def test_openai_responses_non_streaming(client: AsyncClient, created_api_key):
    """Test the OpenAI-compatible non-streaming responses endpoint directly."""
    flow, headers = await load_and_prepare_flow(client, created_api_key)

    # Now test the OpenAI-compatible endpoint
    payload = {"model": flow["id"], "input": "Hello, Langflow!", "stream": False}

    # Make the request
    response = await client.post("/api/v1/responses", json=payload, headers=headers)
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response content: {response.content}")

    # Handle potential errors
    if response.status_code != 200:
        logger.error(f"Error response: {response.content}")
        pytest.fail(f"Request failed with status {response.status_code}")

    try:
        data = response.json()
        if "error" in data and data["error"] is not None:
            logger.error(f"Error in response: {data['error']}")
            # Don't fail immediately, log more details for debugging
            logger.error(f"Full error details: {data}")
            error_msg = "Unknown error"
            if isinstance(data.get("error"), dict):
                error_msg = data["error"].get("message", "Unknown error")
            elif data.get("error"):
                error_msg = str(data["error"])
            pytest.fail(f"Error in response: {error_msg}")

        # Validate the response
        assert "id" in data
        assert "output" in data

        # Validate usage field exists (may be None if LLM doesn't return usage)
        assert "usage" in data
        if data["usage"] is not None:
            logger.info(f"Usage data returned: {data['usage']}")
            assert "input_tokens" in data["usage"]
            assert "output_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]
    except Exception as exc:
        logger.exception("Exception parsing response")
        pytest.fail(f"Failed to parse response: {exc}")