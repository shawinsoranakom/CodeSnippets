def test_add_auth_responses_to_openapi_all_http_methods():
    """Test that all HTTP methods are handled correctly."""
    app = FastAPI()

    from fastapi import Security

    from autogpt_libs.auth.jwt_utils import get_jwt_payload

    @app.get("/resource")
    def get_resource(jwt: dict = Security(get_jwt_payload)):
        return {"method": "GET"}

    @app.post("/resource")
    def post_resource(jwt: dict = Security(get_jwt_payload)):
        return {"method": "POST"}

    @app.put("/resource")
    def put_resource(jwt: dict = Security(get_jwt_payload)):
        return {"method": "PUT"}

    @app.patch("/resource")
    def patch_resource(jwt: dict = Security(get_jwt_payload)):
        return {"method": "PATCH"}

    @app.delete("/resource")
    def delete_resource(jwt: dict = Security(get_jwt_payload)):
        return {"method": "DELETE"}

    # Apply customization
    add_auth_responses_to_openapi(app)

    schema = app.openapi()

    # All methods should have 401 response
    if "/resource" in schema["paths"]:
        for method in ["get", "post", "put", "patch", "delete"]:
            if method in schema["paths"]["/resource"]:
                method_spec = schema["paths"]["/resource"][method]
                if "responses" in method_spec:
                    assert "401" in method_spec["responses"]
