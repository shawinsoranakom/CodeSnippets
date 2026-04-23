def test_template_creation_compatibility(self):
        """Test that template creation still works with dynamic imports."""
        # Test accessing component attributes needed for templates

        # Components should have all necessary attributes for template creation
        assert hasattr(OpenAIModelComponent, "__name__")
        assert hasattr(OpenAIModelComponent, "__module__")
        assert hasattr(OpenAIModelComponent, "display_name")
        assert isinstance(OpenAIModelComponent.display_name, str)
        assert OpenAIModelComponent.display_name
        assert hasattr(OpenAIModelComponent, "description")
        assert isinstance(OpenAIModelComponent.description, str)
        assert OpenAIModelComponent.description
        assert hasattr(OpenAIModelComponent, "icon")
        assert isinstance(OpenAIModelComponent.icon, str)
        assert OpenAIModelComponent.icon
        assert hasattr(OpenAIModelComponent, "inputs")
        assert isinstance(OpenAIModelComponent.inputs, list)
        assert len(OpenAIModelComponent.inputs) > 0
        # Check that each input has required attributes
        for input_field in OpenAIModelComponent.inputs:
            assert hasattr(input_field, "name"), f"Input {input_field} missing 'name' attribute"
            assert hasattr(input_field, "display_name"), f"Input {input_field} missing 'display_name' attribute"