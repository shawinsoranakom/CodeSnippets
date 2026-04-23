def __get_pydantic_json_schema__(  # pylint: disable=W0221
        cls, core_schema, handler
    ) -> dict[str, Any]:
        """Override JSON schema generation to preserve all inherited field properties.

        This method ensures all fields are included in the OpenAPI schema.
        """
        json_schema = handler(core_schema)

        if "properties" not in json_schema or not json_schema["properties"]:
            json_schema["properties"] = {}

            for field_name, field_info in cls.model_fields.items():
                field_schema: dict[str, Any] = {}
                annotation = field_info.annotation

                if hasattr(annotation, "__origin__"):
                    args = getattr(annotation, "__args__", ())

                    if type(None) in args:
                        inner_type = next((a for a in args if a is not type(None)), str)

                        if inner_type is float:
                            field_schema["anyOf"] = [
                                {"type": "number"},
                                {"type": "null"},
                            ]
                        elif inner_type is str:
                            field_schema["anyOf"] = [
                                {"type": "string"},
                                {"type": "null"},
                            ]
                        else:
                            field_schema["anyOf"] = [
                                {"type": "string", "format": "date"},
                                {"type": "null"},
                            ]
                else:
                    field_schema["type"] = "string"

                field_schema["default"] = field_info.default
                field_schema["title"] = (
                    field_info.title or field_name.replace("_", " ").title()
                )

                if field_info.description:
                    field_schema["description"] = field_info.description

                if field_info.json_schema_extra:
                    field_schema.update(field_info.json_schema_extra)  # type: ignore[arg-type]

                json_schema["properties"][field_name] = field_schema

        # Preserve x-widget_config from model_config.json_schema_extra
        config_extra = cls.model_config.get("json_schema_extra", {})
        if "x-widget_config" in config_extra:  # type: ignore[operator]
            json_schema["x-widget_config"] = config_extra["x-widget_config"]  # type: ignore[index]

        return json_schema