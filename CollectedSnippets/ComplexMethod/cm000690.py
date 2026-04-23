async def test_stats_initialization(self):
        """Test that blocks properly initialize stats when not present."""
        import backend.blocks.llm as llm

        block = llm.AIStructuredResponseGeneratorBlock()

        # Initially stats should be initialized with zeros
        assert hasattr(block, "execution_stats")
        assert block.execution_stats.llm_call_count == 0

        # Mock llm_call
        async def mock_llm_call(*args, **kwargs):
            return llm.LLMResponse(
                raw_response="",
                prompt=[],
                response='<json_output id="test123456">{"result": "test"}</json_output>',
                tool_calls=None,
                prompt_tokens=10,
                completion_tokens=20,
                reasoning=None,
            )

        block.llm_call = mock_llm_call  # type: ignore

        # Run the block
        input_data = llm.AIStructuredResponseGeneratorBlock.Input(
            prompt="Test",
            expected_format={"result": "desc"},
            model=llm.DEFAULT_LLM_MODEL,
            credentials=llm.TEST_CREDENTIALS_INPUT,  # type: ignore
        )

        # Run the block
        outputs = {}
        # Mock secrets.token_hex to return consistent ID
        with patch("secrets.token_hex", return_value="test123456"):
            async for output_name, output_data in block.run(
                input_data, credentials=llm.TEST_CREDENTIALS
            ):
                outputs[output_name] = output_data

        # Block finished - now grab and assert stats
        assert block.execution_stats is not None
        assert block.execution_stats.input_token_count == 10
        assert block.execution_stats.output_token_count == 20
        assert block.execution_stats.llm_call_count == 1  # Should have exactly 1 call

        # Check output
        assert "response" in outputs
        assert outputs["response"] == {"result": "test"}