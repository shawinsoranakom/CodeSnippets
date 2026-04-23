def test_add_auth_responses_to_openapi_no_security_endpoints():
    """Test with app that has no secured endpoints."""
    app = FastAPI()

    @app.get("/public1")
    def public1():
        return {"message": "public1"}

    @app.post("/public2")
    def public2():
        return {"message": "public2"}

    # Apply customization
    add_auth_responses_to_openapi(app)

    schema = app.openapi()

    # Component should still be added for consistency
    assert "HTTP401NotAuthenticatedError" in schema["components"]["responses"]

    # But no endpoints should have 401 responses
    for path in schema["paths"].values():
        for method in path.values():
            if isinstance(method, dict) and "responses" in method:
                assert "401" not in method["responses"]
