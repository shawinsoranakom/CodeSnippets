def test_call(self, mistral_tokenizer: MistralTokenizer):
        token_ids = (
            [1, 22177, 4304, 2662]
            if mistral_tokenizer.is_tekken
            else [1, 23325, 2294, 1686]
        )
        attn_mask = [1 for _ in range(len(token_ids))]

        # Test 1: no special tokens
        assert mistral_tokenizer("Hello world !", add_special_tokens=False) == {
            "attention_mask": attn_mask[1:],
            "input_ids": token_ids[1:],
        }
        # Test 2: special tokens
        assert mistral_tokenizer("Hello world !", add_special_tokens=True) == {
            "attention_mask": attn_mask,
            "input_ids": token_ids,
        }
        # Test 3: special tokens + truncation
        assert mistral_tokenizer(
            "Hello world !", add_special_tokens=True, truncation=True, max_length=3
        ) == {
            "attention_mask": attn_mask[:-1],
            "input_ids": token_ids[:-1],
        }
        # Test 4: special tokens + no truncation + max length
        assert mistral_tokenizer(
            "Hello world !", add_special_tokens=True, max_length=3
        ) == {
            "attention_mask": attn_mask,
            "input_ids": token_ids,
        }
        # Test 5: empty string
        assert mistral_tokenizer("", add_special_tokens=False) == {
            "attention_mask": [],
            "input_ids": [],
        }

        with pytest.raises(
            ValueError,
            match=(r"`text_pair` is not supported by `MistralTokenizer.__call__`."),
        ):
            mistral_tokenizer("Hello world !", "invalid pair")