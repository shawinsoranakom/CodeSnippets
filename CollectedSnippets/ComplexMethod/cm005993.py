def test_build_structured_output_data_object_properties(
        self, mock_get_model_class, mock_llm, mock_model_classes, model_metadata
    ):
        """Test that the returned Data object has proper properties."""
        mock_get_model_class.return_value = mock_model_classes(mock_llm)

        def mock_get_chat_result(runnable, system_message, input_value, config, **kwargs):  # noqa: ARG001
            class MockBaseModel(BaseModel):
                def model_dump(self, **__):
                    return {"objects": [{"product": "iPhone", "price": 999.99, "available": True}]}

            return {
                "messages": ["mock_message"],
                "responses": [MockBaseModel()],
                "response_metadata": [{"id": "mock_id"}],
                "attempts": 1,
            }

        component = StructuredOutputComponent(
            model=model_metadata,
            api_key="test-api-key",
            input_value="Product info: iPhone costs $999.99 and is available",
            schema_name="ProductInfo",
            output_schema=[
                {"name": "product", "type": "str", "description": "Product name"},
                {"name": "price", "type": "float", "description": "Product price"},
                {"name": "available", "type": "bool", "description": "Product availability"},
            ],
            multiple=False,
            system_prompt="Extract product info",
        )

        with patch("lfx.components.llm_operations.structured_output.get_chat_result", mock_get_chat_result):
            result = component.build_structured_output()

            # Check that result is a Data object
            from lfx.schema.data import Data

            assert isinstance(result, Data)

            # Check that result.data is a dict with correct types
            assert isinstance(result.data, dict)
            assert isinstance(result.data["product"], str)
            assert isinstance(result.data["price"], float)
            assert isinstance(result.data["available"], bool)

            # Check values
            assert result.data["product"] == "iPhone"
            assert result.data["price"] == 999.99
            assert result.data["available"] is True

            # Test Data object methods if they exist
            if hasattr(result, "get_text"):
                # Data object should be able to represent itself as text
                text_repr = result.get_text()
                assert isinstance(text_repr, str)