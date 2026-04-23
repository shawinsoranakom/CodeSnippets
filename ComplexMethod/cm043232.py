def _extract_single_field(self, element, field):
        """
        Extract a single field based on its type.

        How it works:
        1. Selects the target element using the field's selector.
        2. Extracts the field value based on its type (e.g., text, attribute, regex).
        3. Applies transformations if defined in the schema.

        Args:
            element: The base element to extract the field from.
            field (Dict[str, Any]): The field definition in the schema.

        Returns:
            Any: The extracted field value.
        """

        if "selector" in field:
            selected = self._get_elements(element, field["selector"])
            if not selected:
                return field.get("default")
            selected = selected[0]
        else:
            selected = element

        type_pipeline = field["type"]
        if not isinstance(type_pipeline, list):
            type_pipeline = [type_pipeline]
        value = selected
        for step in type_pipeline:
            if step == "text":
                value = self._get_element_text(value)
            elif step == "attribute":
                value = self._get_element_attribute(value, field["attribute"])
            elif step == "html":
                value = self._get_element_html(value)
            elif step == "regex":
                pattern = field.get("pattern")
                if pattern:
                    # If value is still an element, extract text first (backward compat)
                    if not isinstance(value, str):
                        value = self._get_element_text(value)
                    if isinstance(value, str):
                        match = re.search(pattern, value)
                        value = match.group(field.get("group", 1)) if match else None
                    else:
                        value = None
            if value is None:
                break

        if "transform" in field:
            value = self._apply_transform(value, field["transform"])

        return value if value is not None else field.get("default")