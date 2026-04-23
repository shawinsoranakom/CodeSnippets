def test_run_json_flag_only() -> None:
    """Test that --json flag works independently."""
    with (
        patch("builtins.print") as mock_print,
        patch.object(check_config, "check") as mock_check,
        patch("sys.argv", ["", "--json"]),
    ):
        mock_check.return_value = {
            "except": {"domain1": ["error1", "error2"]},
            "warn": {"domain2": ["warning1"]},
            "components": {"homeassistant": {}, "light": {}, "http": {}},
            "secrets": {},
            "secret_cache": {},
            "yaml_files": {},
        }

        exit_code = check_config.run(None)

        # Should exit with code 1 (1 domain with errors)
        assert exit_code == 1

        # Should have printed JSON
        assert mock_print.call_count == 1
        json_output = mock_print.call_args[0][0]

        # Verify it's valid JSON
        parsed_json = json.loads(json_output)

        # Verify JSON structure
        assert "config_dir" in parsed_json
        assert "total_errors" in parsed_json
        assert "total_warnings" in parsed_json
        assert "errors" in parsed_json
        assert "warnings" in parsed_json
        assert "components" in parsed_json

        # Verify JSON content
        assert parsed_json["total_errors"] == 2  # 2 error messages
        assert parsed_json["total_warnings"] == 1  # 1 warning message
        assert parsed_json["errors"] == {"domain1": ["error1", "error2"]}
        assert parsed_json["warnings"] == {"domain2": ["warning1"]}
        assert set(parsed_json["components"]) == {"homeassistant", "light", "http"}