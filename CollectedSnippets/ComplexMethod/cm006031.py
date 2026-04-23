def test_component_initialization(self, component_class, default_kwargs):
        component = component_class(**default_kwargs)
        frontend_node = component.to_frontend_node()
        node_data = frontend_node["data"]["node"]

        # Test template fields
        template = node_data["template"]
        assert "global_imports" in template
        assert "python_code" in template

        # Test global_imports configuration
        global_imports = template["global_imports"]
        assert global_imports["type"] == "str"
        assert global_imports["value"] == "math"
        assert global_imports["required"] is True

        # Test python_code configuration
        python_code = template["python_code"]
        # assert python_code["type"] == "code"  # TODO: Restore when CodeInput is included in component
        assert python_code["type"] == "str"  # TODO: Remove when CodeInput is included in component
        assert python_code["value"] == "print('Hello, World!')"
        assert python_code["required"] is True

        # Test base configuration - JSON is the new name (Data is alias for backward compatibility)
        assert "JSON" in node_data["base_classes"]