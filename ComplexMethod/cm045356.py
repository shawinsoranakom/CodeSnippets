def _json_schema_to_model(
        self, schema: Dict[str, Any], model_name: str, root_schema: Dict[str, Any]
    ) -> Type[BaseModel]:
        if "allOf" in schema:
            merged: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}
            for s in schema["allOf"]:
                part = self._resolve_ref(s["$ref"], root_schema) if "$ref" in s else s
                merged["properties"].update(part.get("properties", {}))
                merged["required"].extend(part.get("required", []))
            for k, v in schema.items():
                if k not in {"allOf", "properties", "required"}:
                    merged[k] = v
            merged["required"] = list(set(merged["required"]))
            schema = merged

        fields: Dict[str, tuple[Any, FieldInfo]] = {}
        required_fields = set(schema.get("required", []))

        for key, value in schema.get("properties", {}).items():
            if "$ref" in value:
                ref_name = value["$ref"].split("/")[-1]
                field_type = self.get_ref(ref_name)
            elif "anyOf" in value:
                sub_models = self._resolve_union_types(value["anyOf"])
                field_type = Union[tuple(sub_models)]
            elif "oneOf" in value:
                sub_models = self._resolve_union_types(value["oneOf"])
                field_type = Union[tuple(sub_models)]
                if "discriminator" in value:
                    discriminator = value["discriminator"]["propertyName"]
                    field_type = Annotated[field_type, Field(discriminator=discriminator)]
            elif "enum" in value:
                field_type = Literal[tuple(value["enum"])]
            elif "allOf" in value:
                merged = {"type": "object", "properties": {}, "required": []}
                for s in value["allOf"]:
                    part = self._resolve_ref(s["$ref"], root_schema) if "$ref" in s else s
                    merged["properties"].update(part.get("properties", {}))
                    merged["required"].extend(part.get("required", []))
                for k, v in value.items():
                    if k not in {"allOf", "properties", "required"}:
                        merged[k] = v
                merged["required"] = list(set(merged["required"]))
                field_type = self._json_schema_to_model(merged, f"{model_name}_{key}", root_schema)
            elif value.get("type") == "object" and "properties" in value:
                field_type = self._json_schema_to_model(value, f"{model_name}_{key}", root_schema)
            else:
                field_type = self._extract_field_type(key, value, model_name, root_schema)

            if field_type is None:
                raise UnsupportedKeywordError(f"Unsupported or missing type for field `{key}` in `{model_name}`")

            default_value = value.get("default")
            is_required = key in required_fields

            if not is_required and default_value is None:
                field_type = Optional[field_type]

            field_args = {
                "default": default_value if not is_required else ...,
            }
            if "title" in value:
                field_args["title"] = value["title"]
            if "description" in value:
                field_args["description"] = value["description"]

            fields[key] = (
                field_type,
                _make_field(
                    default_value if not is_required else ...,
                    title=value.get("title"),
                    description=value.get("description"),
                ),
            )

        model: Type[BaseModel] = create_model(model_name, **cast(dict[str, Any], fields))
        model.model_rebuild()
        return model