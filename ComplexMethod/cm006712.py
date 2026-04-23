def _build_model(name: str, subschema: dict[str, Any]) -> type[BaseModel]:
        """Create (or fetch) a BaseModel subclass for the given object schema."""
        # If this came via a named $ref, use that name
        if "$ref" in subschema:
            refname = subschema["$ref"].split("/")[-1]
            if refname in model_cache:
                return model_cache[refname]
            # Self-referential: this $ref is already being built — fall back to dict
            if refname in building:
                logger.warning("Parsing input schema: Self-referential $ref '%s' detected, treating as dict", refname)
                return dict  # type: ignore[return-value]
            target = defs.get(refname)
            if not target:
                msg = f"Definition '{refname}' not found"
                raise ValueError(msg)
            building.add(refname)
            try:
                cls = _build_model(refname, target)
            finally:
                building.discard(refname)
            model_cache[refname] = cls
            return cls

        # Named anonymous or inline: avoid clashes by name
        if name in model_cache:
            return model_cache[name]
        # Self-referential: this model name is already being built — fall back to dict
        if name in building:
            logger.warning("Parsing input schema: Self-referential model '%s' detected, treating as dict", name)
            return dict  # type: ignore[return-value]

        building.add(name)
        try:
            props = subschema.get("properties", {})
            reqs = {r for r in (subschema.get("required") or []) if isinstance(r, str)}
            fields: dict[str, Any] = {}

            for prop_name, prop_schema in props.items():
                py_type = parse_type(prop_schema)
                is_required = prop_name in reqs
                if not is_required:
                    py_type = py_type | None
                    default = prop_schema.get("default", None)
                else:
                    default = ...  # required by Pydantic

                # Add alias for camelCase if field name is snake_case
                field_kwargs = {"description": prop_schema.get("description")}
                if "_" in prop_name:
                    camel_case_name = _snake_to_camel(prop_name)
                    if camel_case_name != prop_name:  # Only add alias if it's different
                        field_kwargs["validation_alias"] = AliasChoices(prop_name, camel_case_name)

                fields[prop_name] = (py_type, Field(default, **field_kwargs))

            # Preserve extras unless schema sets additionalProperties:false (#9881, #10975).
            extra_mode = "ignore" if subschema.get("additionalProperties") is False else "allow"
            model_cls = create_model(name, __config__=ConfigDict(extra=extra_mode), **fields)
        finally:
            building.discard(name)
        model_cache[name] = model_cls
        return model_cls