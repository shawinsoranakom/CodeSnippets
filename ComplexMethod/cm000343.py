async def test_block_with_optional_fields(self):
        """Test block with optional input fields."""
        # Optional is already imported at the module level

        class OptionalFieldBlock(Block):
            """Block with optional fields."""

            class Input(BlockSchemaInput):
                required_field: str = SchemaField(description="Required field")
                optional_field: Optional[str] = SchemaField(
                    description="Optional field",
                    default=None,
                )
                optional_with_default: str = SchemaField(
                    description="Optional with default",
                    default="default value",
                )

            class Output(BlockSchemaOutput):
                has_optional: bool = SchemaField(description="Has optional value")
                optional_value: Optional[str] = SchemaField(
                    description="Optional value"
                )
                default_value: str = SchemaField(description="Default value")

            def __init__(self):
                super().__init__(
                    id="optional-field-block",
                    description="Block with optional fields",
                    categories={BlockCategory.TEXT},
                    input_schema=OptionalFieldBlock.Input,
                    output_schema=OptionalFieldBlock.Output,
                )

            async def run(self, input_data: Input, **kwargs) -> BlockOutput:
                yield "has_optional", input_data.optional_field is not None
                yield "optional_value", input_data.optional_field
                yield "default_value", input_data.optional_with_default

        # Test with optional field provided
        block = OptionalFieldBlock()
        outputs = {}
        async for name, value in block.run(
            OptionalFieldBlock.Input(
                required_field="test",
                optional_field="provided",
            )
        ):
            outputs[name] = value

        assert outputs["has_optional"] is True
        assert outputs["optional_value"] == "provided"
        assert outputs["default_value"] == "default value"

        # Test without optional field
        outputs = {}
        async for name, value in block.run(
            OptionalFieldBlock.Input(
                required_field="test",
            )
        ):
            outputs[name] = value

        assert outputs["has_optional"] is False
        assert outputs["optional_value"] is None
        assert outputs["default_value"] == "default value"