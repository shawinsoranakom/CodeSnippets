def extract_reasoning(
        self, model_output: str, request: "ChatCompletionRequest | ResponsesRequest"
    ) -> tuple[str | None, str | None]:
        """Extract the reasoning content & content sections, respectively.
        If the sequence doesn't match what we expect, i.e., the model generates
        something else, all content is considered non-reasoning content.

        Args:
            model_output (str): Output of the model to be parsed.
            request (ChatCompletionRequest): Request being processed.

        Returns:
            tuple[Optional[str], Optional[str]]: Tuple pair containing the
            reasoning content and non-reasoning content.
        """

        re_match = self.full_match_reasoning_regex.findall(model_output)
        if re_match:
            reasoning, response_content = re_match[0]
            if len(reasoning) == 0:
                reasoning = None
            if len(response_content) == 0:
                response_content = None
            return reasoning, response_content

        fallback_regex = self.half_match_reasoning_regex
        fallback_match = fallback_regex.findall(model_output)
        if fallback_match:
            reasoning, response_content = fallback_match[0]

            if response_content.endswith(self.response_end_expr):
                response_content = response_content[: -len(self.response_end_expr)]

            if len(reasoning) == 0:
                reasoning = None
            if len(response_content) == 0:
                response_content = None

            return reasoning, response_content

        return None, model_output