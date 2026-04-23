def test_with_real_openai_model_complex_schema(self):
        # Create a component with a more complex schema using real OpenAI model
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
            Product Review:
            I purchased the XYZ Wireless Headphones last month. The sound quality is excellent,
            and the battery lasts about 8 hours. However, they're a bit uncomfortable after
            wearing them for a long time. The price was $129.99, which I think is reasonable
            for the quality. Overall rating: 4/5.
            """,
            schema_name="ProductReview",
            output_schema=[
                {"name": "product_name", "type": "str", "description": "The name of the product"},
                {"name": "sound_quality", "type": "str", "description": "Description of sound quality"},
                {"name": "comfort", "type": "str", "description": "Description of comfort"},
                {"name": "battery_life", "type": "str", "description": "Description of battery life"},
                {"name": "price", "type": "float", "description": "The price of the product"},
                {"name": "rating", "type": "float", "description": "The overall rating out of 5"},
            ],
            multiple=False,
            system_prompt="Extract detailed product review information from the input text.",
        )

        # Get the structured output
        result = component.build_structured_output_base()

        # Verify the result
        assert isinstance(result, list)
        assert len(result) > 0
        assert "product_name" in result[0]
        assert "sound_quality" in result[0]
        assert "comfort" in result[0]
        assert "battery_life" in result[0]
        assert "price" in result[0]
        assert "rating" in result[0]
        assert result[0]["product_name"] == "XYZ Wireless Headphones"
        assert result[0]["price"] == 129.99
        assert result[0]["rating"] == 4.0