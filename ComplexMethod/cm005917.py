async def test_component_merging_logic(self, mock_settings_service, mock_langflow_components):
        """Test that langflow and custom components are properly merged."""
        # Setup
        mock_settings_service.settings.components_path = ["/custom/path1"]
        mock_settings_service.settings.lazy_load_components = False

        # Create overlapping component names to test merging behavior
        overlapping_custom_components = {
            "category1": {  # Same category as langflow
                "Component1": {"display_name": "CustomComponent1", "type": "category1"},  # Same name as langflow
                "Component4": {"display_name": "Component4", "type": "category1"},  # New component
            },
            "new_category": {
                "NewComponent": {"display_name": "NewComponent", "type": "new_category"},
            },
        }

        with (
            patch("lfx.interface.components.import_langflow_components", return_value=mock_langflow_components),
            patch("lfx.interface.components.aget_all_types_dict", return_value=overlapping_custom_components),
        ):
            # Execute the function
            result = await get_and_cache_all_types_dict(mock_settings_service)

            # Verify that custom components override langflow components with same name
            assert "category1" in result
            assert "category2" in result  # From langflow
            assert "new_category" in result  # From custom

            # Custom category should completely override langflow category
            assert result["category1"]["Component1"]["display_name"] == "CustomComponent1"

            # Only components from custom category should remain in category1
            assert "Component2" not in result["category1"]  # Langflow component is replaced by custom category
            assert "Component4" in result["category1"]  # New custom component

            # New custom component should be added
            assert result["category1"]["Component4"]["display_name"] == "Component4"

            # New category should be added
            assert result["new_category"]["NewComponent"]["display_name"] == "NewComponent"