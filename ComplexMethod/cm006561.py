def test_component_inputs(self, component_class):
        """Test component input definitions."""
        component = component_class()
        inputs_dict = {inp.name: inp for inp in component.inputs}

        # Check API key input
        if "api_key" not in inputs_dict:
            pytest.fail("api_key not found in inputs_dict")
        if inputs_dict["api_key"].display_name != "VLM Run API Key":
            pytest.fail(
                f"Expected api_key display_name to be 'VLM Run API Key', got '{inputs_dict['api_key'].display_name}'"
            )
        if inputs_dict["api_key"].required is not True:
            pytest.fail(f"Expected api_key to be required, got {inputs_dict['api_key'].required}")

        # Check media type input
        if "media_type" not in inputs_dict:
            pytest.fail("media_type not found in inputs_dict")
        if inputs_dict["media_type"].display_name != "Media Type":
            pytest.fail(
                f"Expected media_type display_name to be 'Media Type', got '{inputs_dict['media_type'].display_name}'"
            )
        if inputs_dict["media_type"].options != ["audio", "video"]:
            pytest.fail(
                f"Expected media_type options to be ['audio', 'video'], got {inputs_dict['media_type'].options}"
            )
        if inputs_dict["media_type"].value != "audio":
            pytest.fail(f"Expected media_type value to be 'audio', got '{inputs_dict['media_type'].value}'")

        # Check media files input
        if "media_files" not in inputs_dict:
            pytest.fail("media_files not found in inputs_dict")
        if inputs_dict["media_files"].display_name != "Media Files":
            pytest.fail(
                f"Expected media_files display_name to be 'Media Files', "
                f"got '{inputs_dict['media_files'].display_name}'"
            )
        if inputs_dict["media_files"].is_list is not True:
            pytest.fail(f"Expected media_files.is_list to be True, got {inputs_dict['media_files'].is_list}")
        if inputs_dict["media_files"].required is not False:
            pytest.fail(f"Expected media_files to not be required, got {inputs_dict['media_files'].required}")

        # Check media URL input
        if "media_url" not in inputs_dict:
            pytest.fail("media_url not found in inputs_dict")
        if inputs_dict["media_url"].display_name != "Media URL":
            pytest.fail(
                f"Expected media_url display_name to be 'Media URL', got '{inputs_dict['media_url'].display_name}'"
            )
        if inputs_dict["media_url"].required is not False:
            pytest.fail(f"Expected media_url to not be required, got {inputs_dict['media_url'].required}")
        if inputs_dict["media_url"].advanced is not True:
            pytest.fail(f"Expected media_url to be advanced, got {inputs_dict['media_url'].advanced}")