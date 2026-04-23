def test_run_json_flow_verbose(self, simple_chat_json):
        """Test executing with verbose output."""
        result = runner.invoke(
            app,
            ["run", "-vv", str(simple_chat_json), "Test verbose"],
        )

        # Should succeed
        assert result.exit_code == 0

        # Verbose output should contain diagnostic messages
        assert "Analyzing JSON flow" in result.stderr
        assert "Valid JSON flow file detected" in result.stderr
        assert "Loading and executing JSON flow" in result.stderr
        assert "Preparing graph for execution" in result.stderr

        # Even in verbose mode, output should have the JSON result
        # When using CliRunner, check result.output which contains combined stdout/stderr
        json_output = result.stdout if result.stdout else result.output

        # Find the JSON block by looking for lines that start with { and collecting until }
        json_lines = []
        in_json = False
        brace_count = 0

        for line in json_output.split("\n"):
            line_stripped = line.strip()
            if not in_json and line_stripped.startswith("{"):
                in_json = True
                json_lines = [line]
                brace_count = line.count("{") - line.count("}")
            elif in_json:
                json_lines.append(line)
                brace_count += line.count("{") - line.count("}")
                if brace_count == 0:
                    # Found complete JSON object
                    break

        if json_lines:
            try:
                json_str = "\n".join(json_lines)
                output = json.loads(json_str)
            except json.JSONDecodeError as e:
                pytest.fail(f"Failed to parse JSON: {e}. JSON was: {json_str[:500]}")
        else:
            # If we couldn't find valid JSON, show what we got for debugging
            pytest.fail(f"No valid JSON output found. Output was: {json_output[:500]}")
        assert output["success"] is True
        assert "result" in output
        assert "Test verbose" in output["result"]