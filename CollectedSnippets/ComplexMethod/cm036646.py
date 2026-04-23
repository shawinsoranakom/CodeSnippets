def test_encode(self, mistral_tokenizer: MistralTokenizer):
        token_ids = (
            [1, 22177, 4304, 2662]
            if mistral_tokenizer.is_tekken
            else [1, 23325, 2294, 1686]
        )

        assert mistral_tokenizer.encode("Hello world !") == token_ids
        assert mistral_tokenizer.encode("Hello world !", max_length=3) == token_ids[:-1]
        assert (
            mistral_tokenizer.encode("Hello world !", truncation=True, max_length=3)
            == token_ids[:-1]
        )
        assert (
            mistral_tokenizer.encode("Hello world !", truncation=False, max_length=3)
            == token_ids
        )

        assert (
            mistral_tokenizer.encode("Hello world !", add_special_tokens=True)
            == token_ids
        )
        assert (
            mistral_tokenizer.encode(
                "Hello world !", add_special_tokens=True, max_length=3
            )
            == token_ids[:-1]
        )
        assert (
            mistral_tokenizer.encode(
                "Hello world !", add_special_tokens=True, truncation=False, max_length=3
            )
            == token_ids
        )
        assert (
            mistral_tokenizer.encode("Hello world !", add_special_tokens=False)
            == token_ids[1:]
        )
        assert mistral_tokenizer.encode("", add_special_tokens=False) == []