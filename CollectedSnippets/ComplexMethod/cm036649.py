def test_tokenizer_like_protocol():
    tokenizer = get_tokenizer("gpt2", use_fast=True)
    assert isinstance(tokenizer, PreTrainedTokenizerFast)
    _assert_tokenizer_like(tokenizer)

    tokenizer = get_tokenizer(
        "mistralai/Mistral-7B-Instruct-v0.3",
        tokenizer_mode="mistral",
    )
    assert isinstance(tokenizer, MistralTokenizer)
    _assert_tokenizer_like(tokenizer)

    tokenizer = get_tokenizer("xai-org/grok-2", tokenizer_mode="grok2")
    assert isinstance(tokenizer, Grok2Tokenizer)
    _assert_tokenizer_like(tokenizer)

    tokenizer = get_tokenizer("deepseek-ai/DeepSeek-V3", tokenizer_mode="deepseek_v32")
    assert isinstance(tokenizer, HfTokenizer)

    # Verify it's a fast tokenizer (required for FastIncrementalDetokenizer)
    assert isinstance(tokenizer, PreTrainedTokenizerFast)
    assert "DSV32" in tokenizer.__class__.__name__
    _assert_tokenizer_like(tokenizer)

    tokenizer = get_tokenizer(
        "Qwen/Qwen-VL",
        tokenizer_mode="qwen_vl",
        trust_remote_code=True,
    )
    assert isinstance(tokenizer, HfTokenizer)
    assert "WithoutImagePad" in tokenizer.__class__.__name__