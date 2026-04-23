def get_method(self, method_name: str):
        """Gets the build method for the custom component.

        Returns:
            dict: The build method for the custom component.
        """
        if not self._code:
            return {}

        component_classes = [
            cls for cls in self.tree["classes"] if "Component" in cls["bases"] or "CustomComponent" in cls["bases"]
        ]
        if not component_classes:
            return {}

        # Assume the first Component class is the one we're interested in
        component_class = component_classes[0]
        build_methods = [method for method in component_class["methods"] if method["name"] == (method_name)]

        return build_methods[0] if build_methods else {}