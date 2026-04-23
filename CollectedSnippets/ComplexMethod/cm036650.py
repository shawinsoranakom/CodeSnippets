def test_customized_tokenizer():
    TokenizerRegistry.register("test_tokenizer", __name__, TestTokenizer.__name__)

    tokenizer = TokenizerRegistry.load_tokenizer("test_tokenizer", "abc")
    assert isinstance(tokenizer, TestTokenizer)
    assert tokenizer.path_or_repo_id == "abc"
    assert tokenizer.bos_token_id == 0
    assert tokenizer.eos_token_id == 1
    assert tokenizer.pad_token_id == 2

    tokenizer = get_tokenizer("abc", tokenizer_mode="test_tokenizer")
    assert isinstance(tokenizer, TestTokenizer)
    assert tokenizer.path_or_repo_id == "abc"
    assert tokenizer.bos_token_id == 0
    assert tokenizer.eos_token_id == 1
    assert tokenizer.pad_token_id == 2