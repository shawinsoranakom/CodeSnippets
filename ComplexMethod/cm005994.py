def test_build_structured_dataframe_returns_dataframe_with_multiple_data(
        self, mock_get_model_class, mock_llm, mock_model_classes, model_metadata
    ):
        """Test that build_structured_dataframe() returns DataFrame object with multiple Data items."""
        mock_get_model_class.return_value = mock_model_classes(mock_llm)

        def mock_get_chat_result(runnable, system_message, input_value, config, **kwargs):  # noqa: ARG001
            class MockBaseModel(BaseModel):
                def model_dump(self, **__):
                    return {
                        "objects": [
                            {"name": "John", "age": 30},
                            {"name": "Jane", "age": 25},
                            {"name": "Bob", "age": 35},
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
            input_value="Test input with multiple people",
            schema_name="PersonSchema",
            output_schema=[
                {"name": "name", "type": "str", "description": "Person's name"},
                {"name": "age", "type": "int", "description": "Person's age"},
            ],
            multiple=False,
            system_prompt="Test system prompt",
        )

        with patch("lfx.components.llm_operations.structured_output.get_chat_result", mock_get_chat_result):
            result = component.build_structured_dataframe()

            # Check that result is a DataFrame object
            from lfx.schema.dataframe import DataFrame

            assert isinstance(result, DataFrame)
            assert len(result) == 3
            assert result.iloc[0]["name"] == "John"
            assert result.iloc[0]["age"] == 30
            assert result.iloc[1]["name"] == "Jane"
            assert result.iloc[1]["age"] == 25
            assert result.iloc[2]["name"] == "Bob"
            assert result.iloc[2]["age"] == 35

            # Test conversion back to Data list
            data_list = result.to_data_list()
            assert len(data_list) == 3
            assert data_list[0].data == {"name": "John", "age": 30}
            assert data_list[1].data == {"name": "Jane", "age": 25}
            assert data_list[2].data == {"name": "Bob", "age": 35}