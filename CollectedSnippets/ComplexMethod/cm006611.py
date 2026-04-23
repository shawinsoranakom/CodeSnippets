async def test_run_and_validate_update_outputs_tool_mode(self):
        """Test run_and_validate_update_outputs with tool_mode field."""

        class TestComponent(Component):
            def build(self) -> None:
                pass

        component = TestComponent()

        # Create a frontend node with regular outputs
        original_outputs = [
            {
                "name": "regular_output",
                "type": "str",
                "display_name": "Regular Output",
                "method": "get_output",
                "types": ["Any"],
                "selected": "Any",
                "value": "__UNDEFINED__",
                "cache": True,
                "required_inputs": None,
                "hidden": None,
            }
        ]
        frontend_node = {
            "outputs": original_outputs.copy()  # Make a copy to preserve original
        }

        # Test enabling tool mode
        updated_node = await component.run_and_validate_update_outputs(
            frontend_node=frontend_node.copy(),  # Use a copy to avoid modifying original
            field_name="tool_mode",
            field_value=True,
        )

        # Verify tool output is added and regular output is removed
        assert len(updated_node["outputs"]) == 1
        assert updated_node["outputs"][0]["name"] == TOOL_OUTPUT_NAME
        assert updated_node["outputs"][0]["display_name"] == TOOL_OUTPUT_DISPLAY_NAME

        # Test disabling tool mode - use the original frontend node
        updated_node = await component.run_and_validate_update_outputs(
            frontend_node={"outputs": original_outputs.copy()},  # Use original outputs
            field_name="tool_mode",
            field_value=False,
        )

        # Verify original outputs are restored
        assert len(updated_node["outputs"]) == 1
        # Compare only essential fields instead of the entire dict
        assert updated_node["outputs"][0]["name"] == original_outputs[0]["name"]
        assert updated_node["outputs"][0]["display_name"] == original_outputs[0]["display_name"]
        assert updated_node["outputs"][0]["method"] == original_outputs[0]["method"]
        assert "types" in updated_node["outputs"][0]
        assert "selected" in updated_node["outputs"][0]