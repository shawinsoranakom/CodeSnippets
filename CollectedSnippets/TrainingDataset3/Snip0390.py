def test_add_auth_responses_to_openapi_with_security():
    """Test that 401 responses are added only to secured endpoints."""
    app = FastAPI()

    # Mock endpoint with security
    from fastapi import Security

    from autogpt_libs.auth.dependencies import get_user_id

    @app.get("/secured")
    def secured_endpoint(user_id: str = Security(get_user_id)):
        return {"user_id": user_id}

    @app.post("/also-secured")
    def another_secured(user_id: str = Security(get_user_id)):
        return {"status": "ok"}

    @app.get("/unsecured")
    def unsecured_endpoint():
        return {"public": True}

    # Apply OpenAPI customization
    add_auth_responses_to_openapi(app)

    # Get schema
    schema = app.openapi()

    # Check that secured endpoints have 401 responses
    if "/secured" in schema["paths"]:
        if "get" in schema["paths"]["/secured"]:
            secured_get = schema["paths"]["/secured"]["get"]
            if "responses" in secured_get:
                assert "401" in secured_get["responses"]
                assert (
                    secured_get["responses"]["401"]["$ref"]
                    == "#/components/responses/HTTP401NotAuthenticatedError"
                )

    if "/also-secured" in schema["paths"]:
        if "post" in schema["paths"]["/also-secured"]:
            secured_post = schema["paths"]["/also-secured"]["post"]
            if "responses" in secured_post:
                assert "401" in secured_post["responses"]

    # Check that unsecured endpoint does not have 401 response
    if "/unsecured" in schema["paths"]:
        if "get" in schema["paths"]["/unsecured"]:
            unsecured_get = schema["paths"]["/unsecured"]["get"]
            if "responses" in unsecured_get:
                assert "401" not in unsecured_get.get("responses", {})
