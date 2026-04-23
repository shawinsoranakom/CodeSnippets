def parse_type(s: dict[str, Any] | None) -> Any:
        """Map a JSON Schema subschema to a Python type (possibly nested)."""
        if s is None:
            return None
        s = resolve_ref(s)

        if "anyOf" in s:
            # Handle common pattern for nullable types (anyOf with string and null)
            subtypes = [sub.get("type") for sub in s["anyOf"] if isinstance(sub, dict) and "type" in sub]

            # Check if this is a simple nullable type (e.g., str | None)
            if len(subtypes) == NULLABLE_TYPE_LENGTH and "null" in subtypes:
                # Get the non-null type
                non_null_type = next(t for t in subtypes if t != "null")
                # Map it to Python type
                if isinstance(non_null_type, str):
                    return {
                        "string": str,
                        "integer": int,
                        "number": float,
                        "boolean": bool,
                        "object": dict,
                        "array": list,
                    }.get(non_null_type, Any)
                return Any

            # For other anyOf cases, use the first non-null type
            subtypes = [parse_type(sub) for sub in s["anyOf"]]
            non_null_types = [t for t in subtypes if t is not None and t is not type(None)]
            if non_null_types:
                return non_null_types[0]
            return str

        t = s.get("type", "any")  # Use string "any" as default instead of Any type
        if isinstance(t, list):
            # JSON Schema: "type": ["string", "null"] for nullable
            non_null = [x for x in t if x != "null" and isinstance(x, str)]
            if non_null:
                prim = {
                    "string": str,
                    "integer": int,
                    "number": float,
                    "boolean": bool,
                    "object": dict,
                    "array": list,
                }.get(non_null[0], Any)
                return prim | None if "null" in t else prim
            return Any
        if t == "array":
            item_schema = s.get("items", {})
            schema_type: Any = parse_type(item_schema)
            return list[schema_type]

        if t == "object":
            # Generic object (no properties) ⇒ dict[str, Any] for free-form key-value pairs
            # This preserves nested dictionaries (fixes issue #9881)
            if not s.get("properties"):
                return dict[str, Any]
            # Inline object with defined properties ⇒ nested model
            return _build_model(f"AnonModel{len(model_cache)}", s)

        # primitive fallback
        return {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "object": dict,
            "array": list,
        }.get(t, Any)