def test_build_model_with_pydantic_model_json_schema(self, mock_chat_ollama, component_class, default_kwargs):
        """Test that the format field works with a schema generated from Pydantic's model_json_schema() method.

        This test reproduces the exact use case described in issue #7122:
        https://github.com/langflow-ai/langflow/issues/7122
        """
        from pydantic import BaseModel, Field

        mock_instance = MagicMock()
        mock_chat_ollama.return_value = mock_instance

        # Create a Pydantic model exactly as a user would
        class PersonInfo(BaseModel):
            """Information about a person."""

            name: str = Field(description="The person's full name")
            age: int = Field(ge=0, le=150, description="The person's age")
            email: str = Field(description="Email address")
            city: str = Field(description="City of residence")

        # Generate the schema using Pydantic's model_json_schema() as mentioned in the issue
        pydantic_schema = PersonInfo.model_json_schema()

        # Override format with the Pydantic-generated schema
        kwargs = default_kwargs.copy()
        kwargs["format"] = pydantic_schema

        component = component_class(**kwargs)

        # This should NOT raise an exception (was the bug in issue #7122)
        model = component.build_model()

        # Verify ChatOllama was called with the Pydantic-generated schema
        call_args = mock_chat_ollama.call_args[1]
        assert call_args["format"] == pydantic_schema
        assert call_args["format"]["type"] == "object"
        assert "name" in call_args["format"]["properties"]
        assert "age" in call_args["format"]["properties"]
        assert "email" in call_args["format"]["properties"]
        assert "city" in call_args["format"]["properties"]
        assert call_args["format"]["properties"]["name"]["description"] == "The person's full name"
        assert model == mock_instance