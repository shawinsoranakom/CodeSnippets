def test_openapi_schema_persistence():
    """Test that modifications to OpenAPI schema persist correctly."""
    app = FastAPI()

    from fastapi import Security

    from autogpt_libs.auth.jwt_utils import get_jwt_payload

    @app.get("/test")
    def test_endpoint(jwt: dict = Security(get_jwt_payload)):
        return {"test": True}

    # Apply customization
    add_auth_responses_to_openapi(app)

    # Get schema multiple times
    schema1 = app.openapi()

    # Modify the cached schema (shouldn't affect future calls)
    schema1["info"]["title"] = "Modified Title"

    # Clear cache and get again
    app.openapi_schema = None
    schema2 = app.openapi()

    # Should regenerate with original title
    assert schema2["info"]["title"] == app.title
    assert schema2["info"]["title"] != "Modified Title"
