def test_build_structured_output_returns_data_with_dict(
        self, mock_get_model_class, mock_llm, mock_model_classes, model_metadata
    ):
        """Test that build_structured_output() returns Data object with dict data."""
        mock_get_model_class.return_value = mock_model_classes(mock_llm)

        def mock_get_chat_result(runnable, system_message, input_value, config, **kwargs):  # noqa: ARG001
            class MockBaseModel(BaseModel):
                def model_dump(self, **__):
                    return {"objects": [{"field": "value2", "number": 24}]}  # Return only one object

            # Return trustcall-style response structure
            return {
                "messages": ["mock_message"],
                "responses": [MockBaseModel()],
                "response_metadata": [{"id": "mock_id"}],
                "attempts": 1,
            }

        component = StructuredOutputComponent(
            model=model_metadata,
            api_key="test-api-key",
            input_value="Test input",
            schema_name="TestSchema",
            output_schema=[
                {"name": "field", "type": "str", "description": "A test field"},
                {"name": "number", "type": "int", "description": "A test number"},
            ],
            multiple=False,
            system_prompt="Test system prompt",
        )

        with patch("lfx.components.llm_operations.structured_output.get_chat_result", mock_get_chat_result):
            result = component.build_structured_output()

            # Check that result is a Data object
            from lfx.schema.data import Data

            assert isinstance(result, Data)

            # Check that result.data is a dict
            assert isinstance(result.data, dict)

            # Check the content of the dict
            assert result.data == {"field": "value2", "number": 24}

            # Verify the data has the expected keys
            assert "field" in result.data
            assert "number" in result.data
            assert result.data["field"] == "value2"
            assert result.data["number"] == 24