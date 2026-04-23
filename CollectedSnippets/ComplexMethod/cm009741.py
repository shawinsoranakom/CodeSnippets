def test_lambda_schemas(snapshot: SnapshotAssertion) -> None:
    first_lambda = lambda x: x["hello"]  # noqa: E731
    assert RunnableLambda(first_lambda).get_input_jsonschema() == {
        "title": "RunnableLambdaInput",
        "type": "object",
        "properties": {"hello": {"title": "Hello"}},
        "required": ["hello"],
    }

    second_lambda = lambda x, y: (x["hello"], x["bye"], y["bah"])  # noqa: E731
    assert RunnableLambda(second_lambda).get_input_jsonschema() == {
        "title": "RunnableLambdaInput",
        "type": "object",
        "properties": {"hello": {"title": "Hello"}, "bye": {"title": "Bye"}},
        "required": ["bye", "hello"],
    }

    def get_value(value):  # type: ignore[no-untyped-def] # noqa: ANN001,ANN202
        return value["variable_name"]

    assert RunnableLambda(get_value).get_input_jsonschema() == {
        "title": "get_value_input",
        "type": "object",
        "properties": {"variable_name": {"title": "Variable Name"}},
        "required": ["variable_name"],
    }

    async def aget_value(value):  # type: ignore[no-untyped-def] # noqa: ANN001,ANN202
        return (value["variable_name"], value.get("another"))

    assert RunnableLambda(aget_value).get_input_jsonschema() == {
        "title": "aget_value_input",
        "type": "object",
        "properties": {
            "another": {"title": "Another"},
            "variable_name": {"title": "Variable Name"},
        },
        "required": ["another", "variable_name"],
    }

    async def aget_values(value):  # type: ignore[no-untyped-def] # noqa: ANN001,ANN202
        return {
            "hello": value["variable_name"],
            "bye": value["variable_name"],
            "byebye": value["yo"],
        }

    assert RunnableLambda(aget_values).get_input_jsonschema() == {
        "title": "aget_values_input",
        "type": "object",
        "properties": {
            "variable_name": {"title": "Variable Name"},
            "yo": {"title": "Yo"},
        },
        "required": ["variable_name", "yo"],
    }

    class InputType(TypedDict):
        variable_name: str
        yo: int

    class OutputType(TypedDict):
        hello: str
        bye: str
        byebye: int

    async def aget_values_typed(value: InputType) -> OutputType:
        return {
            "hello": value["variable_name"],
            "bye": value["variable_name"],
            "byebye": value["yo"],
        }

    assert _normalize_schema(
        RunnableLambda(aget_values_typed).get_input_jsonschema()
    ) == _normalize_schema(
        {
            "$defs": {
                "InputType": {
                    "properties": {
                        "variable_name": {
                            "title": "Variable Name",
                            "type": "string",
                        },
                        "yo": {"title": "Yo", "type": "integer"},
                    },
                    "required": ["variable_name", "yo"],
                    "title": "InputType",
                    "type": "object",
                }
            },
            "allOf": [{"$ref": "#/$defs/InputType"}],
            "title": "aget_values_typed_input",
        }
    )

    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(
            RunnableLambda(aget_values_typed).get_output_jsonschema()
        ) == snapshot(name="schema8")