async def test_operational_error_with_metadata(self):
        # Create a mock model that raises an AttributeError during processing
        class ErrorModel:
            def with_config(self, *_, **__):
                return self

            async def abatch(self, *_):
                msg = "Mock error during batch processing"
                raise AttributeError(msg)

        component = BatchRunComponent(
            model=ErrorModel(),
            df=DataFrame({"text": ["test1", "test2"]}),
            column_name="text",
            enable_metadata=True,
        )

        result = await component.run_batch()
        assert isinstance(result, DataFrame)
        assert len(result) == 1  # Component returns a single error row
        error_row = result.iloc[0]
        # Verify error metadata
        assert error_row["metadata"]["processing_status"] == "failed"
        assert "Mock error during batch processing" in error_row["metadata"]["error"]
        # Verify base row structure
        assert error_row["text"] == ""
        assert error_row["model_response"] == ""
        assert error_row["batch_index"] == -1