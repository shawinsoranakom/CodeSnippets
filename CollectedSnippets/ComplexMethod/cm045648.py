def test_column_example():
    test_tags = ["Testing", "Endpoint", "Hello world"]

    class InputSchema(pw.Schema):
        k: int
        v: str = pw.column_definition(
            default_value="Hello", description="Some value", example="Example"
        )

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

    schema_for_post = description["paths"]["/"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]["properties"]

    assert schema_for_post["v"]["description"] == "Some value"
    assert schema_for_post["v"]["example"] == "Example"

    field_found = False
    schema_for_get_parameters = description["paths"]["/"]["get"]["parameters"]
    for parameter in schema_for_get_parameters:
        if parameter["name"] != "v":
            continue
        assert parameter["description"] == "Some value"
        assert parameter["example"] == "Example"
        field_found = True
        break

    assert field_found