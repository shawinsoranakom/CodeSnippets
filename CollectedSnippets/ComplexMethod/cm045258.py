def count_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []) -> int:
        """
        Estimate the number of tokens used by messages and tools.

        Note: This is an estimation based on common tokenization patterns and may not perfectly
        match Anthropic's exact token counting for Claude models.
        """
        # Use cl100k_base encoding as an approximation for Claude's tokenizer
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            encoding = tiktoken.get_encoding("gpt2")  # Fallback

        num_tokens = 0

        # System message tokens (if any)
        system_content = None
        for message in messages:
            if isinstance(message, SystemMessage):
                system_content = message.content
                break

        if system_content:
            num_tokens += len(encoding.encode(system_content)) + 15  # Approximate system message overhead

        # Message tokens
        for message in messages:
            if isinstance(message, SystemMessage):
                continue  # Already counted

            # Base token cost per message
            num_tokens += 10  # Approximate message role & formatting overhead

            # Content tokens
            if isinstance(message, UserMessage) or isinstance(message, AssistantMessage):
                if isinstance(message.content, str):
                    num_tokens += len(encoding.encode(message.content))
                elif isinstance(message.content, list):
                    # Handle different content types
                    for part in message.content:
                        if isinstance(part, str):
                            num_tokens += len(encoding.encode(part))
                        elif isinstance(part, Image):
                            # Estimate vision tokens (simplified)
                            num_tokens += 512  # Rough estimation for image tokens
                        elif isinstance(part, FunctionCall):
                            num_tokens += len(encoding.encode(part.name))
                            num_tokens += len(encoding.encode(part.arguments))
                            num_tokens += 10  # Function call overhead
            elif isinstance(message, FunctionExecutionResultMessage):
                for result in message.content:
                    num_tokens += len(encoding.encode(result.content))
                    num_tokens += 10  # Function result overhead

        # Tool tokens
        for tool in tools:
            if isinstance(tool, Tool):
                tool_schema = tool.schema
            else:
                tool_schema = tool

            # Name and description
            num_tokens += len(encoding.encode(tool_schema["name"]))
            if "description" in tool_schema:
                num_tokens += len(encoding.encode(tool_schema["description"]))

            # Parameters
            if "parameters" in tool_schema:
                params = tool_schema["parameters"]

                if "properties" in params:
                    for prop_name, prop_schema in params["properties"].items():
                        num_tokens += len(encoding.encode(prop_name))

                        if "type" in prop_schema:
                            num_tokens += len(encoding.encode(prop_schema["type"]))

                        if "description" in prop_schema:
                            num_tokens += len(encoding.encode(prop_schema["description"]))

                        # Special handling for enums
                        if "enum" in prop_schema:
                            for value in prop_schema["enum"]:
                                if isinstance(value, str):
                                    num_tokens += len(encoding.encode(value))
                                else:
                                    num_tokens += 2  # Non-string enum values

            # Tool overhead
            num_tokens += 20

        return num_tokens