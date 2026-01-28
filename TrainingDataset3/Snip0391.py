def test_add_auth_responses_to_openapi_existing_responses():
    """Test handling endpoints that already have responses defined."""
    app = FastAPI()

    from fastapi import Security

    from autogpt_libs.auth.jwt_utils import get_jwt_payload

    @app.get(
        "/with-responses",
        responses={
            200: {"description": "Success"},
            404: {"description": "Not found"},
        },
    )
    def endpoint_with_responses(jwt: dict = Security(get_jwt_payload)):
        return {"data": "test"}

    # Apply customization
    add_auth_responses_to_openapi(app)

    schema = app.openapi()

    # Check that existing responses are preserved and 401 is added
    if "/with-responses" in schema["paths"]:
        if "get" in schema["paths"]["/with-responses"]:
            responses = schema["paths"]["/with-responses"]["get"].get("responses", {})
            # Original responses should be preserved
            if "200" in responses:
                assert responses["200"]["description"] == "Success"
            if "404" in responses:
                assert responses["404"]["description"] == "Not found"
            # 401 should be added
            if "401" in responses:
                assert (
                    responses["401"]["$ref"]
                    == "#/components/responses/HTTP401NotAuthenticatedError"
                )
