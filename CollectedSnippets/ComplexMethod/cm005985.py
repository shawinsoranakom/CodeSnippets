async def test_successful_batch_run_with_system_message(self):
        # Create test data
        test_df = DataFrame({"text": ["Hello", "World", "Test"]})

        component = BatchRunComponent(
            model=_MockLLM(),
            system_message="You are a helpful assistant",
            df=test_df,
            column_name="text",
            enable_metadata=True,
        )

        # Run the batch process
        result = await component.run_batch()

        # Verify the results
        assert isinstance(result, DataFrame)
        assert "text" in result.columns
        assert "model_response" in result.columns
        assert "metadata" in result.columns
        assert len(result) == 3
        assert all(isinstance(resp, str) for resp in result["model_response"])
        # Convert DataFrame to list of dicts for easier testing
        result_dicts = result.to_dict("records")
        # Verify metadata
        assert all(row["metadata"]["has_system_message"] for row in result_dicts)
        assert all(row["metadata"]["processing_status"] == "success" for row in result_dicts)