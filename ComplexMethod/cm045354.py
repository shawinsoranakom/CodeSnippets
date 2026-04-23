def _resolve_union_types(self, schemas: List[Dict[str, Any]]) -> List[Any]:
        types: List[Any] = []
        for s in schemas:
            if "$ref" in s:
                types.append(self.get_ref(s["$ref"].split("/")[-1]))
            elif "enum" in s:
                types.append(Literal[tuple(s["enum"])] if len(s["enum"]) > 0 else Any)
            else:
                json_type = s.get("type")
                if json_type not in TYPE_MAPPING:
                    raise UnsupportedKeywordError(f"Unsupported or missing type `{json_type}` in union")

                # Handle array types with items specification
                if json_type == "array" and "items" in s:
                    item_schema = s["items"]
                    if "$ref" in item_schema:
                        item_type = self.get_ref(item_schema["$ref"].split("/")[-1])
                    else:
                        item_type_name = item_schema.get("type")
                        if item_type_name is None:
                            item_type = str
                        elif item_type_name not in TYPE_MAPPING:
                            raise UnsupportedKeywordError(f"Unsupported item type `{item_type_name}` in union array")
                        else:
                            item_type = TYPE_MAPPING[item_type_name]

                    constraints = {}
                    if "minItems" in s:
                        constraints["min_length"] = s["minItems"]
                    if "maxItems" in s:
                        constraints["max_length"] = s["maxItems"]

                    array_type = conlist(item_type, **constraints) if constraints else List[item_type]  # type: ignore[valid-type]
                    types.append(array_type)
                else:
                    types.append(TYPE_MAPPING[json_type])
        return types