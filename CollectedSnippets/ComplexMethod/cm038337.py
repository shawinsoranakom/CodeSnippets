def extract_tool_calls(
        self, model_output: str, request: ChatCompletionRequest
    ) -> ExtractedToolCallInformation:
        """
        Extract the tool calls from a complete model response.
        """

        # remove <|python_start|> and <|python_end|>
        # as Llama 4 model sometime will output those tokens
        if model_output.startswith("<|python_start|>"):
            model_output = model_output[len("<|python_start|>") :]
            model_output = model_output.replace("<|python_end|>", "")

        is_tool_call_pattern = False
        try:
            is_tool_call_pattern = (
                self.TOOL_CALL_REGEX.match(
                    model_output, timeout=envs.VLLM_TOOL_PARSE_REGEX_TIMEOUT_SECONDS
                )
                is not None
            )
        except TimeoutError:
            logger.warning("Regex timeout occurred when matching tool call pattern.")
            logger.debug(
                "Regex timeout occurred when matching user input: %s", model_output
            )

        if not is_tool_call_pattern:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        try:
            module = ast.parse(model_output)
            parsed = getattr(module.body[0], "value", None)
            if isinstance(parsed, ast.List) and all(
                isinstance(e, ast.Call) for e in parsed.elts
            ):
                return ExtractedToolCallInformation(
                    tools_called=True,
                    tool_calls=[
                        handle_single_tool(e)  # type: ignore
                        for e in parsed.elts
                    ],
                    content=None,
                )
            else:
                raise UnexpectedAstError("Tool output must be a list of function calls")
        except Exception:
            logger.exception("Error in extracting tool call from response.")
            # Treat as regular text
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )