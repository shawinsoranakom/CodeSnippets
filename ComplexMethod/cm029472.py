def transform(node: Dict[str, Any], in_object_property: bool = False) -> None:
        node_type = node.get("type")

        if node_type == "object":
            node["additionalProperties"] = False
            properties = node.get("properties") or {}
            if isinstance(properties, dict):
                node["required"] = list(properties.keys())
                for prop in properties.values():
                    if isinstance(prop, dict):
                        transform(prop, in_object_property=True)
            return

        if node_type == "array":
            if in_object_property:
                node["type"] = _nullable_type(node_type)
            items = node.get("items")
            if isinstance(items, dict):
                transform(items, in_object_property=False)
            return

        if in_object_property and node_type is not None:
            node["type"] = _nullable_type(node_type)