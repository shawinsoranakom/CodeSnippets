async def test_component_template_structure(self):
        """Test that component templates have expected structure."""
        langflow_result = await import_langflow_components()

        for category, components in langflow_result["components"].items():
            assert isinstance(components, dict), f"Category {category} should contain dict of components"

            for comp_name, comp_template in components.items():
                assert isinstance(comp_template, dict), f"Component {comp_name} should be a dict"

                if comp_template:
                    expected_fields = {"display_name", "type", "template"}
                    present_fields = set(comp_template.keys())

                    common_fields = expected_fields.intersection(present_fields)
                    if len(common_fields) == 0 and comp_template:
                        print(f"Warning: Component {comp_name} missing expected fields. Has: {list(present_fields)}")