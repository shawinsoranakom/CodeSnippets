def function_call_parsing(cls, data):
        """Parse function_call dictionaries into ResponseFunctionToolCall objects.
        This ensures Pydantic can properly resolve union types in the input field.
        Function calls provided as dicts are converted to ResponseFunctionToolCall
        objects before validation, while invalid structures are left for Pydantic
        to reject with appropriate error messages.
        """

        input_data = data.get("input")

        # Early return for None, strings, or bytes
        # (strings are iterable but shouldn't be processed)
        if input_data is None or isinstance(input_data, (str, bytes)):
            return data

        # Convert iterators (like ValidatorIterator) to list
        if not isinstance(input_data, list):
            try:
                input_data = list(input_data)
            except TypeError:
                # Not iterable, leave as-is for Pydantic to handle
                return data

        processed_input = []
        for item in input_data:
            if isinstance(item, dict) and item.get("type") == "function_call":
                try:
                    processed_input.append(ResponseFunctionToolCall(**item))
                except ValidationError:
                    # Let Pydantic handle validation for malformed function calls
                    logger.debug(
                        "Failed to parse function_call to ResponseFunctionToolCall, "
                        "leaving for Pydantic validation"
                    )
                    processed_input.append(item)
            else:
                processed_input.append(item)

        data["input"] = processed_input
        return data