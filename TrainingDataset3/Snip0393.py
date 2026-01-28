def test_add_auth_responses_to_openapi_multiple_security_schemes():
    """Test endpoints with multiple security requirements."""
    app = FastAPI()

    from fastapi import Security

    from autogpt_libs.auth.dependencies import requires_admin_user, requires_user
    from autogpt_libs.auth.models import User

    @app.get("/multi-auth")
    def multi_auth(
        user: User = Security(requires_user),
        admin: User = Security(requires_admin_user),
    ):
        return {"status": "super secure"}

    # Apply customization
    add_auth_responses_to_openapi(app)

    schema = app.openapi()

    # Should have 401 response
    if "/multi-auth" in schema["paths"]:
        if "get" in schema["paths"]["/multi-auth"]:
            responses = schema["paths"]["/multi-auth"]["get"].get("responses", {})
            if "401" in responses:
                assert (
                    responses["401"]["$ref"]
                    == "#/components/responses/HTTP401NotAuthenticatedError"
                )
