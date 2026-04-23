def test_with_real_openai_model_nested_schema(self):
        # Create a component with a flattened schema (no nested structures) using real OpenAI model
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
            input_value="""
            Restaurant: Bella Italia
            Address: 123 Main St, Anytown, CA 12345
            Visited: June 15, 2023

            Ordered:
            - Margherita Pizza ($14.99) - Delicious with fresh basil
            - Tiramisu ($8.50) - Perfect sweetness

            Service was excellent, atmosphere was cozy.
            Total bill: $35.49 including tip.
            Would definitely visit again!
            """,
            schema_name="RestaurantReview",
            output_schema=[
                {"name": "restaurant_name", "type": "str", "description": "The name of the restaurant"},
                {"name": "street", "type": "str", "description": "Street address"},
                {"name": "city", "type": "str", "description": "City"},
                {"name": "state", "type": "str", "description": "State"},
                {"name": "zip", "type": "str", "description": "ZIP code"},
                {"name": "first_item_name", "type": "str", "description": "Name of first item ordered"},
                {"name": "first_item_price", "type": "float", "description": "Price of first item"},
                {"name": "second_item_name", "type": "str", "description": "Name of second item ordered"},
                {"name": "second_item_price", "type": "float", "description": "Price of second item"},
                {"name": "total_bill", "type": "float", "description": "Total bill amount"},
                {"name": "would_return", "type": "bool", "description": "Whether the reviewer would return"},
            ],
            multiple=False,
            system_prompt="Extract detailed restaurant review information from the input text.",
        )

        # Get the structured output
        result = component.build_structured_output_base()

        # Verify the result
        assert isinstance(result, list)
        assert len(result) > 0
        assert "restaurant_name" in result[0]
        assert "street" in result[0]
        assert "city" in result[0]
        assert "state" in result[0]
        assert "zip" in result[0]
        assert "first_item_name" in result[0]
        assert "first_item_price" in result[0]
        assert "total_bill" in result[0]
        assert "would_return" in result[0]

        assert result[0]["restaurant_name"] == "Bella Italia"
        assert result[0]["street"] == "123 Main St"
        assert result[0]["total_bill"] == 35.49
        assert result[0]["would_return"] is True