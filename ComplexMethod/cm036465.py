def test_is_reasoning_end_streaming(self, test_tokenizer):
        """Test the is_reasoning_end_streaming method."""
        parser = TestThinkingReasoningParser(test_tokenizer)
        end_token_id = parser.end_token_id
        start_token_id = parser.start_token_id

        assert (
            parser.is_reasoning_end_streaming([1, 2, end_token_id], [end_token_id])
            is True
        )
        assert parser.is_reasoning_end_streaming([1, 2, 3, 4], [4]) is False
        assert parser.is_reasoning_end_streaming([], []) is False
        assert (
            parser.is_reasoning_end_streaming(
                [1, start_token_id, 2, end_token_id], [end_token_id]
            )
            is True
        )
        assert (
            parser.is_reasoning_end_streaming([1, start_token_id, 2, 3], [3]) is False
        )
        assert (
            parser.is_reasoning_end_streaming(
                [1, start_token_id, 2, end_token_id, 2, start_token_id, 2],
                [2],
            )
            is False
        )
        assert (
            parser.is_reasoning_end_streaming(
                [1, start_token_id, 2, end_token_id, 2, 2], [2]
            )
            is False
        )