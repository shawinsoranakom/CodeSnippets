def test_advanced_inputs_added(self, component_class):
        """Test that new advanced inputs are properly added."""
        component = component_class()
        inputs_dict = {inp.name: inp for inp in component.inputs}

        # Check timeout_seconds input
        default_timeout = 600
        if "timeout_seconds" not in inputs_dict:
            pytest.fail("timeout_seconds not found in inputs_dict")
        if inputs_dict["timeout_seconds"].display_name != "Timeout (seconds)":
            pytest.fail(
                f"Expected timeout_seconds display_name to be 'Timeout (seconds)', "
                f"got '{inputs_dict['timeout_seconds'].display_name}'"
            )
        if inputs_dict["timeout_seconds"].value != default_timeout:
            pytest.fail(
                f"Expected timeout_seconds value to be {default_timeout}, got {inputs_dict['timeout_seconds'].value}"
            )
        if inputs_dict["timeout_seconds"].advanced is not True:
            pytest.fail(f"Expected timeout_seconds to be advanced, got {inputs_dict['timeout_seconds'].advanced}")

        # Check domain input
        if "domain" not in inputs_dict:
            pytest.fail("domain not found in inputs_dict")
        if inputs_dict["domain"].display_name != "Processing Domain":
            pytest.fail(
                f"Expected domain display_name to be 'Processing Domain', got '{inputs_dict['domain'].display_name}'"
            )
        if inputs_dict["domain"].options != ["transcription"]:
            pytest.fail(f"Expected domain options to be ['transcription'], got {inputs_dict['domain'].options}")
        if inputs_dict["domain"].value != "transcription":
            pytest.fail(f"Expected domain value to be 'transcription', got '{inputs_dict['domain'].value}'")
        if inputs_dict["domain"].advanced is not True:
            pytest.fail(f"Expected domain to be advanced, got {inputs_dict['domain'].advanced}")