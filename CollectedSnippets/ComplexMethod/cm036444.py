def test_resolve_chat_template_kwargs(sample_json_schema, model, expected_kwargs):
    """checks that chat_template is a dict type for HF models."""
    model_info = HF_EXAMPLE_MODELS.find_hf_info(model)
    model_info.check_available_online(on_fail="skip")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "dummy_function_name",
                "description": "This is a dummy function",
                "parameters": sample_json_schema,
            },
        }
    ]

    chat_template_kwargs = {
        # both unused
        "unused_kwargs_1": 123,
        "unused_kwargs_2": "abc",
        # should not appear
        "chat_template": "{% Hello world! %}",
        "tokenize": True,
        # used by tokenizer
        "continue_final_message": True,
        "tools": tools,
        # both used by Qwen2-VL and Qwen3
        "add_generation_prompt": True,
        # only used by Qwen2-VL
        "add_vision_id": True,
        # only used by Qwen3
        "enable_thinking": True,
    }

    model_config = ModelConfig(
        model,
        tokenizer=model_info.tokenizer or model,
        tokenizer_mode=model_info.tokenizer_mode,
        revision=model_info.revision,
        trust_remote_code=model_info.trust_remote_code,
        hf_overrides=model_info.hf_overrides,
        skip_tokenizer_init=model_info.require_embed_inputs,
        enable_prompt_embeds=model_info.require_embed_inputs,
        enable_mm_embeds=model_info.require_embed_inputs,
        enforce_eager=model_info.enforce_eager,
        dtype=model_info.dtype,
    )

    # Build the tokenizer
    tokenizer = get_tokenizer(
        model,
        trust_remote_code=model_config.trust_remote_code,
    )

    # Test detecting the tokenizer's chat_template
    chat_template = resolve_chat_template(
        tokenizer,
        chat_template=None,
        tools=tools,
        model_config=model_config,
    )
    with pytest.raises(
        ValueError, match="Found unexpected chat template kwargs from request"
    ):
        # should raise error if `chat_template_kwargs` contains
        # `chat_template` or `tokenize`
        resolve_chat_template_kwargs(
            tokenizer,
            chat_template=chat_template,
            chat_template_kwargs=chat_template_kwargs,
        )
    resolved_chat_template_kwargs = resolve_chat_template_kwargs(
        tokenizer,
        chat_template=chat_template,
        chat_template_kwargs=chat_template_kwargs,
        raise_on_unexpected=False,
    )
    assert set(resolved_chat_template_kwargs.keys()) == expected_kwargs

    # Additional test: Verify HF base parameters work with **kwargs tokenizers
    # This validates the fix for tokenizers like Kimi K2 that use **kwargs
    # to receive standard HuggingFace parameters instead of declaring them explicitly
    hf_base_params = _get_hf_base_chat_template_params()
    # Verify common HF parameters are in the base class
    assert {"add_generation_prompt", "tools", "continue_final_message"}.issubset(
        hf_base_params
    ), f"Expected HF base params not found in {hf_base_params}"

    # Test with a mock tokenizer that uses **kwargs (like Kimi K2)
    class MockTokenizerWithKwargs:
        def apply_chat_template(self, conversation, **kwargs):
            return "mocked_output"

    mock_tokenizer = MockTokenizerWithKwargs()
    mock_kwargs = {
        "add_generation_prompt": True,
        "tools": tools,
        "continue_final_message": False,
        "unknown_param": "should_be_filtered",
    }
    resolved_mock = resolve_chat_template_kwargs(
        mock_tokenizer, chat_template, mock_kwargs, raise_on_unexpected=False
    )
    # HF base params should pass through even with **kwargs tokenizer
    assert "add_generation_prompt" in resolved_mock
    assert "tools" in resolved_mock
    assert "continue_final_message" in resolved_mock
    # Unknown params should be filtered out
    assert "unknown_param" not in resolved_mock