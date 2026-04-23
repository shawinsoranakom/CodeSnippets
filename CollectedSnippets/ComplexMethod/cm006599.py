def test_run_json_output_format(self, simple_chat_json):
        """Test that JSON output is single-line when not verbose, multi-line when verbose."""
        # Non-verbose mode - should be compact single-line JSON
        result = runner.invoke(
            app,
            ["run", str(simple_chat_json), "Test compact"],
        )

        # Should succeed
        assert result.exit_code == 0

        # Output should be single line (no newlines except at the end)
        assert result.stdout.count("\n") == 1  # Only the trailing newline
        # Should still be valid JSON
        output = json.loads(result.stdout)
        assert output["success"] is True
        assert "Test compact" in output["result"]

        # Verbose mode - should be pretty-printed multi-line JSON
        result_verbose = runner.invoke(
            app,
            ["run", "--verbose", str(simple_chat_json), "Test pretty"],
        )

        # Should succeed
        assert result_verbose.exit_code == 0

        # output should have pretty-printed JSON (multi-line)
        json_output = result_verbose.stdout if result_verbose.stdout else result_verbose.output

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
            pytest.fail("No JSON output found")
        assert output["success"] is True
        assert "Test pretty" in output["result"]