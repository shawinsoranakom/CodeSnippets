def _convert_parameters(self, input_dict):
                    if not input_dict or not isinstance(input_dict, dict):
                        return input_dict

                    converted_dict = {}
                    original_fields = set(self.args_schema.model_fields.keys())

                    for key, value in input_dict.items():
                        if key in original_fields:
                            # Field exists as-is
                            converted_dict[key] = value
                        else:
                            # Try to convert camelCase to snake_case
                            snake_key = _camel_to_snake(key)
                            if snake_key in original_fields:
                                converted_dict[snake_key] = value
                            else:
                                # Keep original key (may be flattened e.g. params.search)
                                converted_dict[key] = value

                    unflattened = maybe_unflatten_dict(converted_dict)
                    # Normalize: convert JSON strings to dict for nested model params
                    normalized = _normalize_arguments_for_mcp(unflattened, self.args_schema, self.name)
                    # Preserve extra keys not in schema (e.g. flattened keys)
                    schema_fields = set(self.args_schema.model_fields.keys())
                    for key, value in unflattened.items():
                        if key not in schema_fields and key not in normalized:
                            normalized[key] = value
                    return normalized