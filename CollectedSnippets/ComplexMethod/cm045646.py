def test_no_extra_fields_on_no_description():
    class InputSchema(pw.Schema):
        k: int
        v: str = pw.column_definition(default_value="hello")

    webserver = pw.io.http.PathwayWebserver(host="127.0.0.1", port=8080)
    pw.io.http.rest_connector(
        webserver=webserver,
        methods=("GET", "POST", "PUT", "PATCH"),
        schema=InputSchema,
        delete_completed_queries=False,
        documentation=pw.io.http.EndpointDocumentation(method_types=("GET", "POST")),
    )

    description = webserver.openapi_description_json("127.0.0.1:8080")
    openapi_spec_validator.validate(description)

    assert set(description["paths"]["/"].keys()) == set(["get", "post"])

    assert "tags" not in description["paths"]["/"]["post"]
    assert "description" not in description["paths"]["/"]["post"]
    assert "summary" not in description["paths"]["/"]["post"]

    assert "tags" not in description["paths"]["/"]["get"]
    assert "description" not in description["paths"]["/"]["get"]
    assert "summary" not in description["paths"]["/"]["get"]