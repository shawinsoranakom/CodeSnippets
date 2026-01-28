def test_add_auth_responses_to_openapi_empty_components():
    """Test when OpenAPI schema has no components section initially."""
    app = FastAPI()

    # Mock get_openapi to return schema without components
    original_get_openapi = get_openapi

    def mock_get_openapi(*args, **kwargs):
        schema = original_get_openapi(*args, **kwargs)
        # Remove components if it exists
        if "components" in schema:
            del schema["components"]
        return schema

    with mock.patch("autogpt_libs.auth.helpers.get_openapi", mock_get_openapi):
        # Apply customization
        add_auth_responses_to_openapi(app)

        schema = app.openapi()

        # Components should be created
        assert "components" in schema
        assert "responses" in schema["components"]
        assert "HTTP401NotAuthenticatedError" in schema["components"]["responses"]
