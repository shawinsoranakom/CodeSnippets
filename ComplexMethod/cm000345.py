async def test_block_error_field_override(self):
        """Test block that overrides the automatic error field from BlockSchemaOutput."""

        class ErrorFieldOverrideBlock(Block):
            """Block that defines its own error field with different type."""

            class Input(BlockSchemaInput):
                value: int = SchemaField(description="Input value")

            class Output(BlockSchemaOutput):
                result: int = SchemaField(description="Result")
                # Override the error field with different description/default but same type
                error: str = SchemaField(
                    description="Custom error field with specific validation codes",
                    default="NO_ERROR",
                )

            def __init__(self):
                super().__init__(
                    id="error-field-override-block",
                    description="Block that overrides the error field",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=ErrorFieldOverrideBlock.Input,
                    output_schema=ErrorFieldOverrideBlock.Output,
                )

            async def run(self, input_data: Input, **kwargs) -> BlockOutput:
                if input_data.value < 0:
                    yield "error", "VALIDATION_ERROR:VALUE_NEGATIVE"
                    yield "result", 0
                else:
                    yield "result", input_data.value * 2
                    yield "error", "NO_ERROR"

        # Test alternative approach: Block that doesn't inherit from BlockSchemaOutput
        class FlexibleErrorBlock(Block):
            """Block that defines its own error structure by not inheriting BlockSchemaOutput."""

            class Input(BlockSchemaInput):
                value: int = SchemaField(description="Input value")

            # Use BlockSchemaInput as base to avoid automatic error field
            class Output(BlockSchema):  # Not BlockSchemaOutput!
                result: int = SchemaField(description="Result")
                error: Optional[dict[str, str]] = SchemaField(
                    description="Structured error information",
                    default=None,
                )

            def __init__(self):
                super().__init__(
                    id="flexible-error-block",
                    description="Block with flexible error structure",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=FlexibleErrorBlock.Input,
                    output_schema=FlexibleErrorBlock.Output,
                )

            async def run(self, input_data: Input, **kwargs) -> BlockOutput:
                if input_data.value < 0:
                    yield "error", {
                        "type": "ValidationError",
                        "message": "Value must be non-negative",
                    }
                    yield "result", 0
                else:
                    yield "result", input_data.value * 2
                    yield "error", None

        # Test 1: String-based error override (constrained by BlockSchemaOutput)
        string_error_block = ErrorFieldOverrideBlock()
        outputs = {}
        async for name, value in string_error_block.run(
            ErrorFieldOverrideBlock.Input(value=5)
        ):
            outputs[name] = value

        assert outputs["result"] == 10
        assert outputs["error"] == "NO_ERROR"

        # Test string error with failure
        outputs = {}
        async for name, value in string_error_block.run(
            ErrorFieldOverrideBlock.Input(value=-3)
        ):
            outputs[name] = value

        assert outputs["result"] == 0
        assert outputs["error"] == "VALIDATION_ERROR:VALUE_NEGATIVE"

        # Test 2: Structured error (using BlockSchema base)
        flexible_block = FlexibleErrorBlock()
        outputs = {}
        async for name, value in flexible_block.run(FlexibleErrorBlock.Input(value=5)):
            outputs[name] = value

        assert outputs["result"] == 10
        assert outputs["error"] is None

        # Test structured error with failure
        outputs = {}
        async for name, value in flexible_block.run(FlexibleErrorBlock.Input(value=-3)):
            outputs[name] = value

        assert outputs["result"] == 0
        assert outputs["error"] == {
            "type": "ValidationError",
            "message": "Value must be non-negative",
        }

        # Verify schema differences
        string_schema = string_error_block.output_schema.jsonschema()
        flexible_schema = flexible_block.output_schema.jsonschema()

        # String error field
        string_error_field = string_schema["properties"]["error"]
        assert string_error_field.get("type") == "string"
        assert string_error_field.get("default") == "NO_ERROR"

        # Structured error field
        flexible_error_field = flexible_schema["properties"]["error"]
        # Should be object or anyOf with object/null for Optional[dict]
        assert (
            "anyOf" in flexible_error_field
            or flexible_error_field.get("type") == "object"
        )