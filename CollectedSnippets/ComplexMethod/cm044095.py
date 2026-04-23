def check_api(
    examples: str, router_name: str, model: str | None, function: Any
) -> list[str]:
    """Check for API examples."""
    api_example_violation: list[str] = []
    parsed_examples = parse_example_string(examples)
    if model and "APIEx" in parsed_examples:
        required_fields = set(get_required_fields(model.strip("'")))
        all_fields = get_all_fields(model.strip("'"))
        all_fields.append("provider")
        required_fields_met = False

        for api_example in parsed_examples["APIEx"]:
            params = ast.literal_eval(api_example.get("params", "{}"))
            if not required_fields_met and required_fields.issubset(params.keys()):
                required_fields_met = True

            # Check for unsupported parameters
            for param in params:
                if param not in all_fields:
                    api_example_violation.append(
                        f"'{router_name}' > '{function.__name__}': param '{param}' is not supported by the command."
                    )

        # If after checking all examples, required fields are still not met
        if not required_fields_met:
            api_example_violation.append(
                f"'{router_name}' > '{function.__name__}': missing example with required fields only > {required_fields}"
            )

    return api_example_violation