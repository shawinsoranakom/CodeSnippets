def preprocess_model_output(
        self, model_output: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Preprocess the model output to extract content and potential tool calls.
        Returns:
            Tuple of (content, potential_tool_calls_json)
        """
        # Check for thinking tag
        thinking_match = re.search(self.thinking_tag_pattern, model_output)
        if thinking_match:
            content = model_output[: thinking_match.start() + len("</think>")].strip()
            thinking_content = thinking_match.group(1).strip()

            # Try to parse the thinking content as JSON
            try:
                json.loads(thinking_content)
                return content, thinking_content
            except json.JSONDecodeError:
                # If can't parse as JSON, look for JSON code blocks
                for json_pattern in self.json_code_block_patterns:
                    json_matches = re.findall(json_pattern, thinking_content)
                    if json_matches:
                        for json_str in json_matches:
                            try:
                                json.loads(json_str)
                                return content, json_str
                            except json.JSONDecodeError:
                                continue

        # Check for JSON code blocks in the entire output
        for json_pattern in self.json_code_block_patterns:
            json_matches = re.findall(json_pattern, model_output)
            if json_matches:
                for json_str in json_matches:
                    try:
                        json.loads(json_str)
                        # Extract content by removing the JSON code block
                        content = re.sub(json_pattern, "", model_output).strip()
                        return content, json_str
                    except json.JSONDecodeError:
                        continue

        # If the entire output is a valid JSON array or looks like one, treat it as tool calls
        if model_output.strip().startswith("["):
            try:
                json.loads(model_output)
                return None, model_output
            except json.JSONDecodeError:
                # Even if it's not valid JSON yet, it might be a tool call in progress
                if (
                    "{" in model_output
                    and "name" in model_output
                    and "arguments" in model_output
                ):
                    return None, model_output

        # If no tool calls found, return the original output as content
        return model_output, None