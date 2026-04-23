def get_test_params(param_fields: dict[str, FieldInfo]) -> dict[str, Any]:
    """Get the test params for the fetcher based on the requires standard params."""
    test_params: dict[str, Any] = {}
    for field_name, field in param_fields.items():
        if field.is_required() and field.default is not PydanticUndefined:
            test_params[field_name] = field.default
        elif field.is_required() or field.default is PydanticUndefined:
            example_dict = {
                "symbol": "AAPL",
                "symbols": "AAPL,MSFT",
                "start_date": date(2023, 1, 1),
                "end_date": date(2023, 6, 6),
                "country": "Portugal",
                "date": date(2023, 1, 1),
                "countries": ["portugal", "spain"],
            }
            if field_name in example_dict:
                test_params[field_name] = example_dict[field_name]
            elif field.annotation is str:
                test_params[field_name] = "test"
            elif field.annotation is int:
                test_params[field_name] = 1
            elif field.annotation is float:
                test_params[field_name] = 1.0
            elif field.annotation is bool:
                test_params[field_name] = True

        # This makes sure that the unit test are reproducible by fixing the date
        elif not field.is_required() and field_name in [
            "start_date",
            "end_date",
            "date",
        ]:
            if field_name == "start_date":
                test_params[field_name] = date(2023, 1, 1)
            elif field_name == "end_date":
                test_params[field_name] = date(2023, 6, 6)
            elif field_name == "date":
                test_params[field_name] = date(2023, 1, 1)
    return test_params