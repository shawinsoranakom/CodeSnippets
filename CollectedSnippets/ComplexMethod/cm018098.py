def test_run_json_output_structure() -> None:
    """Test JSON output contains all required fields with correct types."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json", "--config", "/test/path"]),
    ):
        mock_check.return_value = {
            "except": {"domain1": ["error1", {"config": "bad"}]},
            "warn": {"domain2": ["warning1", {"config": "deprecated"}]},
            "components": {"homeassistant": {}, "light": {}, "automation": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)

        json_output = mock_print.call_args[0][0]
        parsed_json = json.loads(json_output)

        # Should exit with code 1 due to errors
        assert exit_code == 1

        # Test all required fields are present
        required_fields = [
            "config_dir",
            "total_errors",
            "total_warnings",
            "errors",
            "warnings",
            "components",
        ]
        for field in required_fields:
            assert field in parsed_json, f"Missing required field: {field}"

        # Test field types and values
        assert isinstance(parsed_json["config_dir"], str)
        assert isinstance(parsed_json["total_errors"], int)
        assert isinstance(parsed_json["total_warnings"], int)
        assert isinstance(parsed_json["errors"], dict)
        assert isinstance(parsed_json["warnings"], dict)
        assert isinstance(parsed_json["components"], list)

        # Test counts are correct
        assert parsed_json["total_errors"] == 2  # 2 items in domain1 list
        assert parsed_json["total_warnings"] == 2  # 2 items in domain2 list

        # Test components is a list of strings
        assert all(isinstance(comp, str) for comp in parsed_json["components"])
        assert set(parsed_json["components"]) == {
            "homeassistant",
            "light",
            "automation",
        }