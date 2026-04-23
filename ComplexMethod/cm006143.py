async def test_error_response_structure(
        self,
        client: AsyncClient,
        created_api_key,
        mock_settings_dev_api_enabled,  # noqa: ARG002
    ):
        """Test that all error responses have consistent structure."""
        flow_id = str(uuid4())
        request_data = {"flow_id": flow_id, "background": False, "stream": False, "inputs": None}

        headers = {"x-api-key": created_api_key.api_key}
        response = await client.post("api/v2/workflows", json=request_data, headers=headers)

        assert response.status_code == 404
        result = response.json()

        # Verify error structure
        assert "detail" in result
        assert "error" in result["detail"]
        assert "code" in result["detail"]
        assert "message" in result["detail"]
        assert "flow_id" in result["detail"]

        # Verify types
        assert isinstance(result["detail"]["error"], str)
        assert isinstance(result["detail"]["code"], str)
        assert isinstance(result["detail"]["message"], str)
        assert isinstance(result["detail"]["flow_id"], str)