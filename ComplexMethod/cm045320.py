def test_metadata_title_description(converter: _JSONSchemaToPydantic) -> None:
    schema = {
        "title": "CustomerProfile",
        "description": "A profile containing personal and contact info",
        "type": "object",
        "properties": {
            "first_name": {"type": "string", "title": "First Name", "description": "Given name of the user"},
            "age": {"type": "integer", "title": "Age", "description": "Age in years"},
            "contact": {
                "type": "object",
                "title": "Contact Information",
                "description": "How to reach the user",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "title": "Email Address",
                        "description": "Primary email",
                    }
                },
            },
        },
        "required": ["first_name"],
    }

    Model: Type[BaseModel] = converter.json_schema_to_pydantic(schema, "CustomerProfile")
    generated_schema = Model.model_json_schema()

    assert generated_schema["title"] == "CustomerProfile"

    props = generated_schema["properties"]
    assert props["first_name"]["title"] == "First Name"
    assert props["first_name"]["description"] == "Given name of the user"
    assert props["age"]["title"] == "Age"
    assert props["age"]["description"] == "Age in years"

    contact = props["contact"]
    assert contact["title"] == "Contact Information"
    assert contact["description"] == "How to reach the user"

    # Follow the $ref
    ref_key = contact["anyOf"][0]["$ref"].split("/")[-1]
    contact_def = generated_schema["$defs"][ref_key]
    email = contact_def["properties"]["email"]
    assert email["title"] == "Email Address"
    assert email["description"] == "Primary email"