def get_model_params(param_fields: dict[str, FieldInfo]) -> dict[str, Any]:
    """Get the test params for the fetcher based on the required standard params."""
    test_params: dict[str, Any] = {}
    for field_name, field in param_fields.items():
        if field.default and field.default is not PydanticUndefined:
            test_params[field_name] = field.default
        elif not field.default or field.default is PydanticUndefined:
            example_dict = {
                "symbol": "AAPL",
                "symbols": "AAPL,MSFT",
                "start_date": "2023-01-01",
                "end_date": "2023-06-06",
                "country": "Portugal",
                "date": "2023-01-01",
                "countries": ["portugal", "spain"],
            }
            if field_name in example_dict:
                test_params[field_name] = example_dict[field_name]
            elif field.annotation is str:
                test_params[field_name] = "TEST_STRING"
            elif field.annotation is int:
                test_params[field_name] = 1
            elif field.annotation is float:
                test_params[field_name] = 1.0
            elif field.annotation is bool:
                test_params[field_name] = True
            elif get_origin(field.annotation) is Literal:
                test_params[field_name] = field.annotation.__args__[0]  # type: ignore

    return test_params