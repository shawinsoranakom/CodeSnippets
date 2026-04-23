def test_extended_description():
    test_tags = ["Testing", "Endpoint", "Hello world"]

    class InputSchema(pw.Schema):
        k: int
        v: str = pw.column_definition(default_value="hello")

    webserver = pw.io.http.PathwayWebserver(host="127.0.0.1", port=8080)
    pw.io.http.rest_connector(
        webserver=webserver,
        methods=("GET", "POST", "PUT", "PATCH"),
        schema=InputSchema,
        delete_completed_queries=False,
        documentation=pw.io.http.EndpointDocumentation(
            description="Endpoint description",
            summary="Endpoint summary",
            tags=test_tags,
            method_types=("GET", "POST"),
        ),
    )

    description = webserver.openapi_description_json("127.0.0.1:8080")
    openapi_spec_validator.validate(description)

    assert set(description["paths"]["/"].keys()) == set(["get", "post"])

    assert description["paths"]["/"]["post"]["tags"] == test_tags
    assert description["paths"]["/"]["post"]["description"] == "Endpoint description"
    assert description["paths"]["/"]["post"]["summary"] == "Endpoint summary"

    assert description["paths"]["/"]["get"]["tags"] == test_tags
    assert description["paths"]["/"]["get"]["description"] == "Endpoint description"
    assert description["paths"]["/"]["get"]["summary"] == "Endpoint summary"