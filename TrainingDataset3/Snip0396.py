def test_endpoint_without_responses_section():
    """Test endpoint that has security but no responses section initially."""
    app = FastAPI()

    from fastapi import Security
    from fastapi.openapi.utils import get_openapi as original_get_openapi

    from autogpt_libs.auth.jwt_utils import get_jwt_payload

    # Create endpoint
    @app.get("/no-responses")
    def endpoint_without_responses(jwt: dict = Security(get_jwt_payload)):
        return {"data": "test"}

    # Mock get_openapi to remove responses from the endpoint
    def mock_get_openapi(*args, **kwargs):
        schema = original_get_openapi(*args, **kwargs)
        # Remove responses from our endpoint to trigger line 40
        if "/no-responses" in schema.get("paths", {}):
            if "get" in schema["paths"]["/no-responses"]:
                # Delete responses to force the code to create it
                if "responses" in schema["paths"]["/no-responses"]["get"]:
                    del schema["paths"]["/no-responses"]["get"]["responses"]
        return schema

    with mock.patch("autogpt_libs.auth.helpers.get_openapi", mock_get_openapi):
        # Apply customization
        add_auth_responses_to_openapi(app)

        # Get schema and verify 401 was added
        schema = app.openapi()

        # The endpoint should now have 401 response
        if "/no-responses" in schema["paths"]:
            if "get" in schema["paths"]["/no-responses"]:
                responses = schema["paths"]["/no-responses"]["get"].get("responses", {})
                assert "401" in responses
                assert (
                    responses["401"]["$ref"]
                    == "#/components/responses/HTTP401NotAuthenticatedError"
                )
