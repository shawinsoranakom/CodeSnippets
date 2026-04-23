def no_invalid_types(case: schemathesis.models.Case):
        """
        This filter skips test cases with invalid data that schemathesis
        incorrectly generates due to permissive schema configurations.

        1. Skips `POST /tokenize` endpoint cases with `"type": "file"` in 
           message content, which isn't implemented.

        2. Skips tool_calls with `"type": "custom"` which schemathesis 
           incorrectly generates instead of the valid `"type": "function"`.

        Example test cases that are skipped:
        curl -X POST -H 'Content-Type: application/json' \
            -d '{"messages": [{"content": [{"file": {}, "type": "file"}], "role": "user"}]}' \
            http://localhost:8000/tokenize

        curl -X POST -H 'Content-Type: application/json' \
            -d '{"messages": [{"role": "assistant", "tool_calls": [{"custom": {"input": "", "name": ""}, "id": "", "type": "custom"}]}]}' \
            http://localhost:8000/v1/chat/completions
        """  # noqa: E501
        if hasattr(case, "body") and isinstance(case.body, dict):
            if (
                "messages" in case.body
                and isinstance(case.body["messages"], list)
                and len(case.body["messages"]) > 0
            ):
                for message in case.body["messages"]:
                    if not isinstance(message, dict):
                        continue

                    # Check for invalid file type in tokenize endpoint
                    if op.method.lower() == "post" and op.path == "/tokenize":
                        content = message.get("content", [])
                        if (
                            isinstance(content, list)
                            and len(content) > 0
                            and any(
                                isinstance(item, dict) and item.get("type") == "file"
                                for item in content
                            )
                        ):
                            return False

                    # Check for invalid tool_calls with non-function types
                    tool_calls = message.get("tool_calls", [])
                    if isinstance(tool_calls, list):
                        for tool_call in tool_calls:
                            if isinstance(tool_call, dict):
                                if tool_call.get("type") != "function":
                                    return False
                                if "custom" in tool_call:
                                    return False

            # Sometimes structured_outputs.grammar is generated to be empty
            # Causing a server error in EBNF grammar parsing
            # https://github.com/vllm-project/vllm/pull/22587#issuecomment-3195253421
            structured_outputs = case.body.get("structured_outputs", {})
            grammar = (
                structured_outputs.get("grammar")
                if isinstance(structured_outputs, dict)
                else None
            )

            if grammar == "":
                # Allow None (will be handled as no grammar)
                # But skip empty strings
                return False

        return True