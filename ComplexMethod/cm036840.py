async def test_streaming_n_gt1_independent_tool_parsers():
    """n>1 streaming must use independent parser instances
    and token-id histories per choice.
    """
    mock_engine = MagicMock(spec=AsyncLLM)
    mock_engine.errored = False
    mock_engine.model_config = MockModelConfig()
    mock_engine.input_processor = MagicMock()
    mock_engine.renderer = _build_renderer(mock_engine.model_config)

    models = OpenAIServingModels(
        engine_client=mock_engine,
        base_model_paths=BASE_MODEL_PATHS,
    )
    openai_serving_render = _build_serving_render(mock_engine, models.registry)

    serving_chat = OpenAIServingChat(
        mock_engine,
        models,
        response_role="assistant",
        openai_serving_render=openai_serving_render,
        chat_template=CHAT_TEMPLATE,
        chat_template_content_format="auto",
        request_logger=None,
        enable_auto_tools=True,
        tool_parser="hermes",
    )

    tokenizer = get_tokenizer(MODEL_NAME)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]

    num_choices = 2

    request = ChatCompletionRequest(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "test"}],
        n=num_choices,
        stream=True,
        tools=tools,
        tool_choice="auto",
    )

    tool_call_text = (
        "<tool_call>\n"
        '{"name": "get_weather", "arguments": {"city": "Tokyo"}}\n'
        "</tool_call>"
    )
    all_token_ids = tokenizer.encode(tool_call_text, add_special_tokens=False)

    # Compute proper delta text for each token so that concatenated deltas
    # reproduce the original string exactly.
    steps: list[tuple[str, int]] = []
    prev_decoded = ""
    for i, tid in enumerate(all_token_ids):
        decoded_so_far = tokenizer.decode(all_token_ids[: i + 1])
        delta = decoded_so_far[len(prev_decoded) :]
        steps.append((delta, tid))
        prev_decoded = decoded_so_far

    async def result_generator():
        for delta_text, token_id in steps:
            yield RequestOutput(
                request_id="test-req",
                prompt="test",
                prompt_token_ids=[1, 2, 3],
                prompt_logprobs=None,
                outputs=[
                    CompletionOutput(
                        index=choice_idx,
                        text=delta_text,
                        token_ids=[token_id],
                        cumulative_logprob=0.0,
                        logprobs=None,
                    )
                    for choice_idx in range(num_choices)
                ],
                finished=False,
            )
        # Final output with finish_reason
        yield RequestOutput(
            request_id="test-req",
            prompt="test",
            prompt_token_ids=[1, 2, 3],
            prompt_logprobs=None,
            outputs=[
                CompletionOutput(
                    index=choice_idx,
                    text="",
                    token_ids=[],
                    cumulative_logprob=0.0,
                    logprobs=None,
                    finish_reason="stop",
                )
                for choice_idx in range(num_choices)
            ],
            finished=True,
        )

    # Collect tool-call deltas per choice from the SSE stream.
    tc_deltas_by_choice: dict[int, list[dict]] = {i: [] for i in range(num_choices)}
    async for chunk_str in serving_chat.chat_completion_stream_generator(
        request=request,
        result_generator=result_generator(),
        request_id="test-req",
        model_name=MODEL_NAME,
        conversation=[],
        tokenizer=tokenizer,
        request_metadata=RequestResponseMetadata(
            request_id="test-req",
            model_name=MODEL_NAME,
        ),
    ):
        if not chunk_str.strip() or "data: [DONE]" in chunk_str:
            continue
        if chunk_str.startswith("data: "):
            data = json.loads(chunk_str[6:].strip())
            for choice in data.get("choices", []):
                idx = choice["index"]
                delta = choice.get("delta", {})
                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        tc_deltas_by_choice[idx].append(tc)

    # Both choices must independently produce the correct tool call.
    for choice_idx in range(num_choices):
        deltas = tc_deltas_by_choice[choice_idx]
        assert len(deltas) > 0, (
            f"Choice {choice_idx}: expected tool-call deltas but got none"
        )

        name = None
        args_buf = ""
        for tc in deltas:
            fn = tc.get("function", {})
            if fn.get("name"):
                name = fn["name"]
            if fn.get("arguments"):
                args_buf += fn["arguments"]

        assert name == "get_weather", (
            f"Choice {choice_idx}: expected 'get_weather', got {name!r}"
        )
        parsed_args = json.loads(args_buf)
        assert parsed_args == {"city": "Tokyo"}, (
            f"Choice {choice_idx}: expected {{'city': 'Tokyo'}}, got {parsed_args}"
        )