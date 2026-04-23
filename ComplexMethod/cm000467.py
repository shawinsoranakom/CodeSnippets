def _filter_secrets_from_node_input(
        input_data: BlockInput, schema: dict[str, Any] | None
    ) -> BlockInput:
        sensitive_keys = ["credentials", "api_key", "password", "token", "secret"]
        field_schemas = schema.get("properties", {}) if schema else {}
        result = {}
        for key, value in input_data.items():
            field_schema: dict | None = field_schemas.get(key)
            if (field_schema and field_schema.get("secret", False)) or (
                any(sensitive_key in key.lower() for sensitive_key in sensitive_keys)
                # Prevent removing `secret` flag on input nodes
                and type(value) is not bool
            ):
                # This is a secret value -> filter this key-value pair out
                continue
            elif isinstance(value, dict):
                result[key] = NodeModel._filter_secrets_from_node_input(
                    value, field_schema
                )
            else:
                result[key] = value
        return result