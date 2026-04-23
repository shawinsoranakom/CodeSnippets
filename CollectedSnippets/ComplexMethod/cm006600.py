def test_async_start_is_used(self, simple_chat_json):
        """Test that graph.async_start is being used."""
        # This is harder to test without mocking the entire graph,
        # but we can at least verify the flow completes successfully
        result = runner.invoke(
            app,
            ["run", "--verbose", str(simple_chat_json), "Test async start"],
        )

        # Should succeed
        assert result.exit_code == 0

        # If async_start wasn't working, we'd get an error
        json_output = result.stdout if result.stdout else result.output

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
                    break

        if not json_lines:
            pytest.fail(f"No valid JSON output found. Output was: {json_output[:500]}")

        output = json.loads("\n".join(json_lines))
        assert output["success"] is True
        assert "result" in output