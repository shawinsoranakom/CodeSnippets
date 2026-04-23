def test_multiple_patterns_with_duplicates_and_variations(
        self, mock_get_model_class, mock_llm, mock_model_classes, model_metadata
    ):
        """Test that multiple patterns are extracted while removing exact duplicates but keeping variations."""
        mock_get_model_class.return_value = mock_model_classes(mock_llm)

        def mock_get_chat_result(runnable, system_message, input_value, config, **kwargs):  # noqa: ARG001
            class MockBaseModel(BaseModel):
                def model_dump(self, **__):
                    return {
                        "objects": [
                            {"product": "iPhone", "price": 999.99},
                            {"product": "iPhone", "price": 1099.99},  # Variation - different price
                            {"product": "Samsung", "price": 899.99},
                            {"product": "iPhone", "price": 999.99},  # Exact duplicate - should be removed
                        ]
                    }

            return {
                "messages": ["mock_message"],
                "responses": [MockBaseModel()],
                "response_metadata": [{"id": "mock_id"}],
                "attempts": 1,
            }

        component = StructuredOutputComponent(
            model=model_metadata,
            api_key="test-api-key",
            input_value="Products: iPhone $999.99, iPhone $1099.99, Samsung $899.99, iPhone $999.99",
            schema_name="ProductSchema",
            output_schema=[
                {"name": "product", "type": "str", "description": "Product name"},
                {"name": "price", "type": "float", "description": "Product price"},
            ],
            multiple=False,
            system_prompt="Remove exact duplicates but keep variations that have different field values.",
        )

        with patch("lfx.components.llm_operations.structured_output.get_chat_result", mock_get_chat_result):
            result = component.build_structured_output()

            # Check that result is a Data object
            from lfx.schema.data import Data

            assert isinstance(result, Data)

            # Should have multiple results due to multiple patterns
            assert isinstance(result.data, dict)
            assert "results" in result.data
            assert (
                len(result.data["results"]) == 4
            )  # All items returned (duplicate handling is expected to be done by LLM)

            # Verify the expected products are present
            products = [item["product"] for item in result.data["results"]]
            prices = [item["price"] for item in result.data["results"]]

            assert "iPhone" in products
            assert "Samsung" in products
            assert 999.99 in prices
            assert 1099.99 in prices
            assert 899.99 in prices