def test_with_real_openai_model_multiple_patterns(self):
        # Create a component with multiple people in the input using real OpenAI model
        component = StructuredOutputComponent(
            model=[
                {
                    "name": "gpt-4o-mini",
                    "provider": "OpenAI",
                    "metadata": {
                        "model_class": "ChatOpenAI",
                        "model_name_param": "model",
                        "api_key_param": "api_key",
                    },
                }
            ],
            api_key=os.getenv("OPENAI_API_KEY"),
            input_value=(
                "Extract all people from this text: John Doe is 30 years old, Jane Smith is 25, and Bob Johnson is 35."
            ),
            schema_name="PersonInfo",
            output_schema=[
                {"name": "name", "type": "str", "description": "The person's name"},
                {"name": "age", "type": "int", "description": "The person's age"},
            ],
            multiple=False,
            system_prompt=(
                "You are an AI that extracts structured JSON objects from unstructured text. "
                "Use a predefined schema with expected types (str, int, float, bool, dict). "
                "Extract ALL relevant instances that match the schema - if multiple patterns exist, capture them all. "
                "Fill missing or ambiguous values with defaults: null for missing values. "
                "Remove exact duplicates but keep variations that have different field values. "
                "Always return valid JSON in the expected format, never throw errors. "
                "If multiple objects can be extracted, return them all in the structured format."
            ),
        )

        # Get the structured output
        result = component.build_structured_output_base()

        # Verify the result contains multiple people
        assert isinstance(result, list)
        assert len(result) >= 3  # Should extract all three people

        # Check that we have names and ages for multiple people
        names = [item["name"] for item in result if "name" in item]
        ages = [item["age"] for item in result if "age" in item]

        assert len(names) >= 3
        assert len(ages) >= 3

        # Check that we extracted the expected people (order may vary)
        expected_names = ["John Doe", "Jane Smith", "Bob Johnson"]
        expected_ages = [30, 25, 35]

        for expected_name in expected_names:
            assert any(expected_name in name for name in names)
        for expected_age in expected_ages:
            assert expected_age in ages