def test_add_auth_responses_to_openapi_basic():
    """Test adding 401 responses to OpenAPI schema."""
    app = FastAPI(title="Test App", version="1.0.0")

    # Add some test endpoints with authentication
    from fastapi import Depends

    from autogpt_libs.auth.dependencies import requires_user

    @app.get("/protected", dependencies=[Depends(requires_user)])
    def protected_endpoint():
        return {"message": "Protected"}

    @app.get("/public")
    def public_endpoint():
        return {"message": "Public"}

    # Apply the OpenAPI customization
    add_auth_responses_to_openapi(app)

    # Get the OpenAPI schema
    schema = app.openapi()

    # Verify basic schema properties
    assert schema["info"]["title"] == "Test App"
    assert schema["info"]["version"] == "1.0.0"

    # Verify 401 response component is added
    assert "components" in schema
    assert "responses" in schema["components"]
    assert "HTTP401NotAuthenticatedError" in schema["components"]["responses"]

    # Verify 401 response structure
    error_response = schema["components"]["responses"]["HTTP401NotAuthenticatedError"]
    assert error_response["description"] == "Authentication required"
    assert "application/json" in error_response["content"]
    assert "schema" in error_response["content"]["application/json"]

    # Verify schema properties
    response_schema = error_response["content"]["application/json"]["schema"]
    assert response_schema["type"] == "object"
    assert "detail" in response_schema["properties"]
    assert response_schema["properties"]["detail"]["type"] == "string"
