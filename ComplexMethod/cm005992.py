def test_build_structured_output_returns_multiple_objects(
        self, mock_get_model_class, mock_llm, mock_model_classes, model_metadata
    ):
        """Test that build_structured_output() returns Data object with multiple objects wrapped in results."""
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
            input_value="Extract multiple people: John is 30, Jane is 25, Bob is 35",
            schema_name="PersonSchema",
            output_schema=[
                {"name": "name", "type": "str", "description": "Person's name"},
                {"name": "age", "type": "int", "description": "Person's age"},
            ],
            multiple=False,
            system_prompt="Extract ALL relevant instances that match the schema",
        )

        with patch("lfx.components.llm_operations.structured_output.get_chat_result", mock_get_chat_result):
            result = component.build_structured_output()

            # Check that result is a Data object
            from lfx.schema.data import Data

            assert isinstance(result, Data)

            # Check that result.data is a dict with results key
            assert isinstance(result.data, dict)
            assert "results" in result.data
            assert len(result.data["results"]) == 3

            # Check the content of each result
            assert result.data["results"][0] == {"name": "John", "age": 30}
            assert result.data["results"][1] == {"name": "Jane", "age": 25}
            assert result.data["results"][2] == {"name": "Bob", "age": 35}