def validate_input_variables(cls, values: dict) -> Any:
        """Validate input variables.

        If `input_variables` is not set, it will be set to the union of all input
        variables in the messages.

        Args:
            values: values to validate.

        Returns:
            Validated values.

        Raises:
            ValueError: If input variables do not match.
        """
        messages = values["messages"]
        input_vars: set = set()
        optional_variables = set()
        input_types: dict[str, Any] = values.get("input_types", {})
        for message in messages:
            if isinstance(message, (BaseMessagePromptTemplate, BaseChatPromptTemplate)):
                input_vars.update(message.input_variables)
            if isinstance(message, MessagesPlaceholder):
                if "partial_variables" not in values:
                    values["partial_variables"] = {}
                if (
                    message.optional
                    and message.variable_name not in values["partial_variables"]
                ):
                    values["partial_variables"][message.variable_name] = []
                    optional_variables.add(message.variable_name)
                if message.variable_name not in input_types:
                    input_types[message.variable_name] = list[AnyMessage]
        if "partial_variables" in values:
            input_vars -= set(values["partial_variables"])
        if optional_variables:
            input_vars -= optional_variables
        if "input_variables" in values and values.get("validate_template"):
            if input_vars != set(values["input_variables"]):
                msg = (
                    "Got mismatched input_variables. "
                    f"Expected: {input_vars}. "
                    f"Got: {values['input_variables']}"
                )
                raise ValueError(msg)
        else:
            values["input_variables"] = sorted(input_vars)
        if optional_variables:
            values["optional_variables"] = sorted(optional_variables)
        values["input_types"] = input_types
        return values