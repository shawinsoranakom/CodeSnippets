async def test_ai_structured_response_block_tracks_stats(self):
        """Test that AIStructuredResponseGeneratorBlock correctly tracks stats."""
        from unittest.mock import patch

        import backend.blocks.llm as llm

        block = llm.AIStructuredResponseGeneratorBlock()

        # Mock the llm_call method
        async def mock_llm_call(*args, **kwargs):
            return llm.LLMResponse(
                raw_response="",
                prompt=[],
                response='<json_output id="test123456">{"key1": "value1", "key2": "value2"}</json_output>',
                tool_calls=None,
                prompt_tokens=15,
                completion_tokens=25,
                reasoning=None,
            )

        block.llm_call = mock_llm_call  # type: ignore

        # Run the block
        input_data = llm.AIStructuredResponseGeneratorBlock.Input(
            prompt="Test prompt",
            expected_format={"key1": "desc1", "key2": "desc2"},
            model=llm.DEFAULT_LLM_MODEL,
            credentials=llm.TEST_CREDENTIALS_INPUT,  # type: ignore  # type: ignore
        )

        outputs = {}
        # Mock secrets.token_hex to return consistent ID
        with patch("secrets.token_hex", return_value="test123456"):
            async for output_name, output_data in block.run(
                input_data, credentials=llm.TEST_CREDENTIALS
            ):
                outputs[output_name] = output_data

        # Check stats
        assert block.execution_stats.input_token_count == 15
        assert block.execution_stats.output_token_count == 25
        assert block.execution_stats.llm_call_count == 1
        assert block.execution_stats.llm_retry_count == 0

        # Check output
        assert "response" in outputs
        assert outputs["response"] == {"key1": "value1", "key2": "value2"}