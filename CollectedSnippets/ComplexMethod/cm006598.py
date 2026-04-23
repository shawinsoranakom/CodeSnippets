def test_run_error_cases(self):
        """Test various error cases."""
        # No input source
        result = runner.invoke(app, ["execute"])
        assert result.exit_code == 2  # Typer returns 2 for missing required arguments
        # Typer's error message will be different from our custom message

        # Non-existent file
        result = runner.invoke(app, ["run", "does_not_exist.json"])
        assert result.exit_code == 1
        # Without verbose, error should be JSON in stdout
        # Extract the last line which should be the JSON error
        lines = result.stdout.strip().split("\n")
        json_line = lines[-1] if lines else ""
        if json_line:
            error_output = json.loads(json_line)
            assert error_output["success"] is False
            assert "exception_message" in error_output, f"Got: {error_output}"
            assert "does not exist" in error_output["exception_message"], f"Got: {error_output}"

        # Invalid file extension
        result = runner.invoke(app, ["run", "test.txt"])
        assert result.exit_code == 1
        # Without verbose, error should be JSON in stdout
        # Extract the last line which should be the JSON error
        lines = result.stdout.strip().split("\n")
        json_line = lines[-1] if lines else ""
        if json_line:
            error_output = json.loads(json_line)
            assert error_output["success"] is False
            # The error could be either "does not exist" or "must be a .py or .json file"
            # depending on whether the file exists
            assert "exception_message" in error_output, f"Got: {error_output}"
            assert (
                "does not exist" in error_output["exception_message"]
                or "must be a .py or .json file" in error_output["exception_message"]
            ), f"Got: {error_output}"

        # Multiple input sources
        result = runner.invoke(
            app,
            ["run", "--stdin", "--flow-json", '{"data": {}}', "test"],
        )
        assert result.exit_code == 1
        # Without verbose, error should be JSON in stdout
        lines = result.stdout.strip().split("\n")
        json_line = lines[-1] if lines else ""
        if json_line:
            error_output = json.loads(json_line)
            assert error_output["success"] is False
            assert "exception_message" in error_output, f"Got: {error_output}"
            assert "Multiple input sources" in error_output["exception_message"], f"Got: {error_output}"