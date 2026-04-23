def json_schema_to_pydantic(
        self, schema: Dict[str, Any], model_name: str = "GeneratedModel", root_schema: Optional[Dict[str, Any]] = None
    ) -> Type[BaseModel]:
        if root_schema is None:
            root_schema = schema
            self._process_definitions(root_schema)

        if "$ref" in schema:
            resolved = self._resolve_ref(schema["$ref"], root_schema)
            schema = {**resolved, **{k: v for k, v in schema.items() if k != "$ref"}}

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

        return self._json_schema_to_model(schema, model_name, root_schema)