def test_file_path_str_input_exists_for_tool_mode(self):
        """Test that file_path_str input exists for tool mode."""
        component = FileComponent()

        # Find the file_path_str input
        file_path_str_input = None
        for input_field in component.inputs:
            if input_field.name == "file_path_str":
                file_path_str_input = input_field
                break

        assert file_path_str_input is not None, "file_path_str input should exist"
        assert file_path_str_input.tool_mode is True, "file_path_str should have tool_mode=True"

        # Check that the path FileInput has tool_mode=False
        path_input = None
        for input_field in component.inputs:
            if input_field.name == "path":
                path_input = input_field
                break

        assert path_input is not None, "path input should exist"
        assert path_input.tool_mode is False, "path FileInput should have tool_mode=False"