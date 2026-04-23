def _walk(
        name: str,
        schema: dict[str, Any],
        *,
        inherited_req: bool,
        _visiting_refs: frozenset[str] = frozenset(),
    ) -> None:
        # Resolve $ref while tracking which refs are currently being expanded
        visited: set[str] = set()
        while "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in _visiting_refs or ref_name in visited:
                logger.warning(
                    "Flattening schema: circular/self-referential $ref '%s' detected, skipping field '%s'",
                    ref_name,
                    name,
                )
                return  # Self-referential schema — stop recursion
            visited.add(ref_name)
            resolved = defs.get(ref_name)
            if resolved is None:
                logger.warning("Flattening schema: definition '%s' not found, skipping field '%s'", ref_name, name)
                return
            schema = resolved
        # Merge newly resolved refs into the visiting set for nested calls
        new_visiting = _visiting_refs | visited

        t = schema.get("type")

        # ── objects ─────────────────────────────────────────────────────────
        if t == "object":
            req_here = set(schema.get("required", []))
            for k, subschema in schema.get("properties", {}).items():
                child_name = f"{name}.{k}" if name else k
                _walk(
                    name=child_name,
                    schema=subschema,
                    inherited_req=inherited_req and k in req_here,
                    _visiting_refs=new_visiting,
                )
            return

        # ── arrays (always recurse into the first item as "[0]") ───────────
        if t == "array":
            items = schema.get("items", {})
            _walk(name=f"{name}[0]", schema=items, inherited_req=inherited_req, _visiting_refs=new_visiting)
            return

        leaf: dict[str, Any] = {
            k: v
            for k, v in schema.items()
            if k
            in (
                "type",
                "description",
                "pattern",
                "format",
                "enum",
                "default",
                "minLength",
                "maxLength",
                "minimum",
                "maximum",
                "exclusiveMinimum",
                "exclusiveMaximum",
                "additionalProperties",
                "examples",
            )
        }
        flat_props[name] = leaf
        if inherited_req:
            required_list.append(name)