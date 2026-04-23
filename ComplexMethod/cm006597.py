def test_run_json_flow_different_formats(self, simple_chat_json, fmt):
        """Test different output formats."""
        result = runner.invoke(
            app,
            ["run", "-f", fmt, str(simple_chat_json), f"Test {fmt} format"],
        )

        # Should succeed
        assert result.exit_code == 0
        assert len(result.stdout) > 0

        if fmt == "json":
            # Should be valid JSON
            output = json.loads(result.stdout)
            assert output["success"] is True
            assert "result" in output
            assert f"Test {fmt} format" in output["result"]
        else:
            # For other formats, check output contains the message
            assert f"Test {fmt} format" in result.stdout