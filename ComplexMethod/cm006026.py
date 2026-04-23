def test_dynamic_outputs_have_tool_mode_enabled(self):
        """Test that all dynamically created outputs have tool_mode=True."""
        component = FileComponent()

        # Test single CSV file
        frontend_node = {"outputs": [], "template": {"path": {"file_path": ["test.csv"]}}}
        result = component.update_outputs(frontend_node, "path", ["test.csv"])
        for output in result["outputs"]:
            assert output.tool_mode is True, f"Output {output.name} should have tool_mode=True"

        # Test single JSON file
        frontend_node = {"outputs": [], "template": {"path": {"file_path": ["data.json"]}}}
        result = component.update_outputs(frontend_node, "path", ["data.json"])
        for output in result["outputs"]:
            assert output.tool_mode is True, f"Output {output.name} should have tool_mode=True"

        # Test multiple files
        frontend_node = {"outputs": [], "template": {"path": {"file_path": ["file1.txt", "file2.txt"]}}}
        result = component.update_outputs(frontend_node, "path", ["file1.txt", "file2.txt"])
        for output in result["outputs"]:
            assert output.tool_mode is True, f"Output {output.name} should have tool_mode=True"

        # Test advanced mode enabled
        frontend_node = {
            "outputs": [],
            "template": {
                "path": {"file_path": ["document.pdf"]},
                "advanced_mode": {"value": True},
            },
        }
        result = component.update_outputs(frontend_node, "advanced_mode", field_value=True)
        for output in result["outputs"]:
            assert output.tool_mode is True, f"Output {output.name} should have tool_mode=True"

        # Test advanced mode disabled
        frontend_node = {
            "outputs": [],
            "template": {
                "path": {"file_path": ["document.pdf"]},
                "advanced_mode": {"value": False},
            },
        }
        result = component.update_outputs(frontend_node, "advanced_mode", field_value=False)
        for output in result["outputs"]:
            assert output.tool_mode is True, f"Output {output.name} should have tool_mode=True"