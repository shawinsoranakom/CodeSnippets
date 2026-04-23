async def test_ai_list_generator_basic_functionality(self):
        """Test that AIListGeneratorBlock correctly works with structured responses."""
        import backend.blocks.llm as llm

        block = llm.AIListGeneratorBlock()

        # Mock the llm_call to return a structured response
        async def mock_llm_call(input_data, credentials):
            # Update stats to simulate LLM call
            block.execution_stats = NodeExecutionStats(
                input_token_count=50,
                output_token_count=30,
                llm_call_count=1,
            )
            # Return a structured response with the expected format
            return {"list": ["item1", "item2", "item3"]}

        block.llm_call = mock_llm_call  # type: ignore

        # Run the block
        input_data = llm.AIListGeneratorBlock.Input(
            focus="test items",
            model=llm.DEFAULT_LLM_MODEL,
            credentials=llm.TEST_CREDENTIALS_INPUT,  # type: ignore
            max_retries=3,
        )

        outputs = {}
        async for output_name, output_data in block.run(
            input_data, credentials=llm.TEST_CREDENTIALS
        ):
            outputs[output_name] = output_data

        # Check stats
        assert block.execution_stats.input_token_count == 50
        assert block.execution_stats.output_token_count == 30
        assert block.execution_stats.llm_call_count == 1

        # Check output
        assert outputs["generated_list"] == ["item1", "item2", "item3"]
        # Check that individual items were yielded
        # Note: outputs dict will only contain the last value for each key
        # So we need to check that the list_item output exists
        assert "list_item" in outputs
        # The list_item output should be the last item in the list
        assert outputs["list_item"] == "item3"
        assert "prompt" in outputs