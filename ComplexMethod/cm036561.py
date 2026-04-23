def test_tool_detection_skip_special_tokens_false(self, parser):
        """Regression: skip_special_tokens must be False when tools are enabled."""
        # adjust_request must set skip_special_tokens=False
        tool = make_tool_param(
            "search",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
            },
        )
        request = make_request(tools=[tool])
        request.tool_choice = "auto"
        adjusted = parser.adjust_request(request)
        assert adjusted.skip_special_tokens is False

        full_text = build_tool_call("search", {"query": "vllm documentation"})

        # Non-streaming extraction
        non_stream_result = parser.extract_tool_calls(full_text, request)
        assert non_stream_result.tools_called
        assert len(non_stream_result.tool_calls) == 1
        assert non_stream_result.tool_calls[0].function.name == "search"
        ns_args = json.loads(non_stream_result.tool_calls[0].function.arguments)
        assert ns_args == {"query": "vllm documentation"}

        # Streaming extraction: drive the parser line-by-line
        chunks: list[str] = []
        remaining = full_text
        while remaining:
            nl = remaining.find("\n")
            if nl == -1:
                chunks.append(remaining)
                break
            chunks.append(remaining[: nl + 1])
            remaining = remaining[nl + 1 :]

        reconstructor = run_tool_extraction_streaming(
            parser, chunks, request, assert_one_tool_per_delta=False
        )
        assert len(reconstructor.tool_calls) == 1
        assert reconstructor.tool_calls[0].function.name == "search"
        streamed_args = json.loads(reconstructor.tool_calls[0].function.arguments)
        assert streamed_args == ns_args