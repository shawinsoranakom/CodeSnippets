def test_components_with_existing_responses():
    """Test when components already has a responses section."""
    app = FastAPI()

    # Mock get_openapi to return schema with existing components/responses
    from fastapi.openapi.utils import get_openapi as original_get_openapi

    def mock_get_openapi(*args, **kwargs):
        schema = original_get_openapi(*args, **kwargs)
        # Add existing components/responses
        if "components" not in schema:
            schema["components"] = {}
        schema["components"]["responses"] = {
            "ExistingResponse": {"description": "An existing response"}
        }
        return schema

    with mock.patch("autogpt_libs.auth.helpers.get_openapi", mock_get_openapi):
        # Apply customization
        add_auth_responses_to_openapi(app)

        schema = app.openapi()

        # Both responses should exist
        assert "ExistingResponse" in schema["components"]["responses"]
        assert "HTTP401NotAuthenticatedError" in schema["components"]["responses"]

        # Verify our 401 response structure
        error_response = schema["components"]["responses"][
            "HTTP401NotAuthenticatedError"
        ]
        assert error_response["description"] == "Authentication required"
