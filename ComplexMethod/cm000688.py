async def test_ai_text_summarizer_multiple_chunks(self):
        """Test that AITextSummarizerBlock correctly accumulates stats across multiple chunks."""
        import backend.blocks.llm as llm

        block = llm.AITextSummarizerBlock()

        # Track calls to simulate multiple chunks
        call_count = 0

        async def mock_llm_call(input_data, credentials):
            nonlocal call_count
            call_count += 1

            # Create a mock block with stats to merge from
            mock_structured_block = llm.AIStructuredResponseGeneratorBlock()
            mock_structured_block.execution_stats = NodeExecutionStats(
                input_token_count=25,
                output_token_count=15,
                llm_call_count=1,
            )

            # Simulate merge_llm_stats behavior
            block.merge_llm_stats(mock_structured_block)

            if "final_summary" in input_data.expected_format:
                return {"final_summary": "Final combined summary"}
            else:
                return {"summary": f"Summary of chunk {call_count}"}

        block.llm_call = mock_llm_call  # type: ignore

        # Create long text that will be split into chunks
        long_text = " ".join(["word"] * 1000)  # Moderate size to force ~2-3 chunks

        input_data = llm.AITextSummarizerBlock.Input(
            text=long_text,
            model=llm.DEFAULT_LLM_MODEL,
            credentials=llm.TEST_CREDENTIALS_INPUT,  # type: ignore
            max_tokens=100,  # Small chunks
            chunk_overlap=10,
        )

        # Run the block
        outputs = {}
        async for output_name, output_data in block.run(
            input_data, credentials=llm.TEST_CREDENTIALS
        ):
            outputs[output_name] = output_data

        # Block finished - now grab and assert stats
        assert block.execution_stats is not None
        assert call_count > 1  # Should have made multiple calls
        assert block.execution_stats.llm_call_count > 0
        assert block.execution_stats.input_token_count > 0
        assert block.execution_stats.output_token_count > 0

        # Check output
        assert "summary" in outputs
        assert outputs["summary"] == "Final combined summary"