def test_tool_calling():
    """
    Test that tool calling works correctly in run_batch.
    Verifies that requests with tools return tool_calls in the response.
    """
    with (
        tempfile.NamedTemporaryFile("w") as input_file,
        tempfile.NamedTemporaryFile("r") as output_file,
    ):
        input_file.write(INPUT_TOOL_CALLING_BATCH)
        input_file.flush()
        proc = subprocess.Popen(
            [
                "vllm",
                "run-batch",
                "-i",
                input_file.name,
                "-o",
                output_file.name,
                "--model",
                REASONING_MODEL_NAME,
                "--enable-auto-tool-choice",
                "--tool-call-parser",
                "hermes",
            ],
        )
        proc.communicate()
        proc.wait()
        assert proc.returncode == 0, f"{proc=}"

        contents = output_file.read()
        for line in contents.strip().split("\n"):
            if not line.strip():  # Skip empty lines
                continue
            # Ensure that the output format conforms to the openai api.
            # Validation should throw if the schema is wrong.
            BatchRequestOutput.model_validate_json(line)

            # Ensure that there is no error in the response.
            line_dict = json.loads(line)
            assert isinstance(line_dict, dict)
            assert line_dict["error"] is None

            # Check that tool_calls are present in the response
            # With tool_choice="required", the model must call a tool
            response_body = line_dict["response"]["body"]
            assert response_body is not None
            message = response_body["choices"][0]["message"]
            assert "tool_calls" in message
            tool_calls = message.get("tool_calls")
            # With tool_choice="required", tool_calls must be present and non-empty
            assert tool_calls is not None
            assert isinstance(tool_calls, list)
            assert len(tool_calls) > 0
            # Verify tool_calls have the expected structure
            for tool_call in tool_calls:
                assert "id" in tool_call
                assert "type" in tool_call
                assert tool_call["type"] == "function"
                assert "function" in tool_call
                assert "name" in tool_call["function"]
                assert "arguments" in tool_call["function"]
                # Verify the tool name matches our tool definition
                assert tool_call["function"]["name"] == "get_current_weather"