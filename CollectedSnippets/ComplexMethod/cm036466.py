def test_different_token_implementations(self, test_tokenizer):
        """
        Test that different implementations
        with different tokens work independently.
        """
        parser1 = TestThinkingReasoningParser(test_tokenizer)
        parser2 = TestThinkingReasoningParserAlt(test_tokenizer)

        # Test parser1
        model_output1 = "Reasoning1</test:think>Content1"
        reasoning1, content1 = run_reasoning_extraction(parser1, [model_output1])
        assert reasoning1 == "Reasoning1"
        assert content1 == "Content1"

        # Test parser2
        model_output2 = "Reasoning2<alt:end>Content2"
        reasoning2, content2 = run_reasoning_extraction(parser2, [model_output2])
        assert reasoning2 == "Reasoning2"
        assert content2 == "Content2"

        # Verify tokens are different
        assert parser1.start_token != parser2.start_token
        assert parser1.end_token != parser2.end_token
        assert parser1.start_token_id != parser2.start_token_id
        assert parser1.end_token_id != parser2.end_token_id