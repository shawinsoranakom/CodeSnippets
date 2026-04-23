def _build_properties(
        title: str, additional_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build properties object for page creation."""
        properties: Dict[str, Any] = {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        }

        if additional_properties:
            for key, value in additional_properties.items():
                if key.lower() == "title":
                    continue  # Skip title as we already have it

                # Try to intelligently map property types
                if isinstance(value, bool):
                    properties[key] = {"checkbox": value}
                elif isinstance(value, (int, float)):
                    properties[key] = {"number": value}
                elif isinstance(value, list):
                    # Assume multi-select
                    properties[key] = {
                        "multi_select": [{"name": str(item)} for item in value]
                    }
                elif isinstance(value, str):
                    # Could be select, rich_text, or other types
                    # For simplicity, try common patterns
                    if key.lower() in ["status", "priority", "type", "category"]:
                        properties[key] = {"select": {"name": value}}
                    elif key.lower() in ["url", "link"]:
                        properties[key] = {"url": value}
                    elif key.lower() in ["email"]:
                        properties[key] = {"email": value}
                    else:
                        properties[key] = {
                            "rich_text": [{"type": "text", "text": {"content": value}}]
                        }

        return properties