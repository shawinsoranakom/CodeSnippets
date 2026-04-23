def _extract_field_type(self, key: str, value: Dict[str, Any], model_name: str, root_schema: Dict[str, Any]) -> Any:
        json_type = value.get("type")
        if json_type not in TYPE_MAPPING:
            raise UnsupportedKeywordError(
                f"Unsupported or missing type `{json_type}` for field `{key}` in `{model_name}`"
            )

        base_type = TYPE_MAPPING[json_type]
        constraints: Dict[str, Any] = {}

        if json_type == "string":
            if "minLength" in value:
                constraints["min_length"] = value["minLength"]
            if "maxLength" in value:
                constraints["max_length"] = value["maxLength"]
            if "pattern" in value:
                constraints["pattern"] = value["pattern"]
            if constraints:
                base_type = constr(**constraints)

        elif json_type == "integer":
            if "minimum" in value:
                constraints["ge"] = value["minimum"]
            if "maximum" in value:
                constraints["le"] = value["maximum"]
            if "exclusiveMinimum" in value:
                constraints["gt"] = value["exclusiveMinimum"]
            if "exclusiveMaximum" in value:
                constraints["lt"] = value["exclusiveMaximum"]
            if constraints:
                base_type = conint(**constraints)

        elif json_type == "number":
            if "minimum" in value:
                constraints["ge"] = value["minimum"]
            if "maximum" in value:
                constraints["le"] = value["maximum"]
            if "exclusiveMinimum" in value:
                constraints["gt"] = value["exclusiveMinimum"]
            if "exclusiveMaximum" in value:
                constraints["lt"] = value["exclusiveMaximum"]
            if constraints:
                base_type = confloat(**constraints)

        elif json_type == "array":
            if "minItems" in value:
                constraints["min_length"] = value["minItems"]
            if "maxItems" in value:
                constraints["max_length"] = value["maxItems"]
            item_schema = value.get("items", {"type": "string"})
            if "$ref" in item_schema:
                item_type = self.get_ref(item_schema["$ref"].split("/")[-1])
            elif item_schema.get("type") == "object" and "properties" in item_schema:
                # Handle array items that are objects with properties - create a nested model
                # Use hash-based naming to keep names short and unique
                item_model_name = self._get_item_model_name(key, model_name)
                item_type = self._json_schema_to_model(item_schema, item_model_name, root_schema)
            else:
                item_type_name = item_schema.get("type")
                if item_type_name is None:
                    item_type = str
                elif item_type_name not in TYPE_MAPPING:
                    raise UnsupportedKeywordError(
                        f"Unsupported or missing item type `{item_type_name}` for array field `{key}` in `{model_name}`"
                    )
                else:
                    item_type = TYPE_MAPPING[item_type_name]

            base_type = conlist(item_type, **constraints) if constraints else List[item_type]  # type: ignore[valid-type]

        if "format" in value:
            format_type = FORMAT_MAPPING.get(value["format"])
            if format_type is None:
                raise FormatNotSupportedError(f"Unknown format `{value['format']}` for `{key}` in `{model_name}`")
            if not isinstance(format_type, type):
                return format_type
            if not issubclass(format_type, str):
                return format_type
            return format_type

        return base_type