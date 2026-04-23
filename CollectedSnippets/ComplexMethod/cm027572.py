def selector_serializer(schema: Any) -> Any:  # noqa: C901
    """Convert selectors into OpenAPI schema."""
    if not isinstance(schema, selector.Selector):
        return UNSUPPORTED

    if isinstance(schema, selector.BackupLocationSelector):
        return {"type": "string", "pattern": "^(?:\\/backup|\\w+)$"}

    if isinstance(schema, selector.BooleanSelector):
        return {"type": "boolean"}

    if isinstance(schema, selector.ColorRGBSelector):
        return {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 3,
            "maxItems": 3,
            "format": "RGB",
        }

    if isinstance(schema, selector.ConditionSelector):
        return convert(cv.CONDITIONS_SCHEMA)

    if isinstance(schema, selector.ConstantSelector):
        return convert(vol.Schema(schema.config["value"]))

    result: dict[str, Any]
    if isinstance(schema, selector.ColorTempSelector):
        result = {"type": "number"}
        if "min" in schema.config:
            result["minimum"] = schema.config["min"]
        elif "min_mireds" in schema.config:
            result["minimum"] = schema.config["min_mireds"]
        if "max" in schema.config:
            result["maximum"] = schema.config["max"]
        elif "max_mireds" in schema.config:
            result["maximum"] = schema.config["max_mireds"]
        return result

    if isinstance(schema, selector.CountrySelector):
        if schema.config.get("countries"):
            return {"type": "string", "enum": schema.config["countries"]}
        return {"type": "string", "format": "ISO 3166-1 alpha-2"}

    if isinstance(schema, selector.DateSelector):
        return {"type": "string", "format": "date"}

    if isinstance(schema, selector.DateTimeSelector):
        return {"type": "string", "format": "date-time"}

    if isinstance(schema, selector.DurationSelector):
        return convert(cv.time_period_dict)

    if isinstance(schema, selector.EntitySelector):
        if schema.config.get("multiple"):
            return {"type": "array", "items": {"type": "string", "format": "entity_id"}}

        return {"type": "string", "format": "entity_id"}

    if isinstance(schema, selector.LanguageSelector):
        if schema.config.get("languages"):
            return {"type": "string", "enum": schema.config["languages"]}
        return {"type": "string", "format": "RFC 5646"}

    if isinstance(schema, selector.LocationSelector):
        return convert(schema.DATA_SCHEMA)

    if isinstance(schema, selector.MediaSelector):
        item_schema = convert(schema.DATA_SCHEMA)
        # Media selector allows multiple when configured
        if schema.config.get("multiple"):
            return {
                "type": "array",
                "items": item_schema,
            }
        return item_schema

    if isinstance(schema, selector.NumberSelector):
        result = {"type": "number"}
        if "min" in schema.config:
            result["minimum"] = schema.config["min"]
        if "max" in schema.config:
            result["maximum"] = schema.config["max"]
        return result

    if isinstance(schema, selector.ObjectSelector):
        result = {"type": "object"}
        if fields := schema.config.get("fields"):
            properties = {}
            required = []
            for field, field_schema in fields.items():
                properties[field] = convert(
                    selector.selector(field_schema["selector"]),
                    custom_serializer=selector_serializer,
                )
                if field_schema.get("required"):
                    required.append(field)
            result["properties"] = properties

            if required:
                result["required"] = required
        else:
            result["additionalProperties"] = True
        if schema.config.get("multiple"):
            result = {
                "type": "array",
                "items": result,
            }
        return result

    if isinstance(schema, selector.SelectSelector):
        options = [
            x["value"] if isinstance(x, dict) else x for x in schema.config["options"]
        ]
        if schema.config.get("multiple"):
            return {
                "type": "array",
                "items": {"type": "string", "enum": options},
                "uniqueItems": True,
            }
        return {"type": "string", "enum": options}

    if isinstance(schema, selector.TargetSelector):
        return convert(cv.TARGET_FIELDS)

    if isinstance(schema, selector.TemplateSelector):
        return {"type": "string", "format": "jinja2"}

    if isinstance(schema, selector.TimeSelector):
        return {"type": "string", "format": "time"}

    if isinstance(schema, selector.TriggerSelector):
        return {"type": "array", "items": {"type": "string"}}

    if schema.config.get("multiple"):
        return {"type": "array", "items": {"type": "string"}}

    return {"type": "string"}