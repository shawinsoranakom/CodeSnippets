async def test_block_error_handling(self):
        """Test block error handling."""

        class ErrorHandlingBlock(Block):
            """Block that demonstrates error handling."""

            class Input(BlockSchemaInput):
                value: int = SchemaField(description="Input value")
                should_error: bool = SchemaField(
                    description="Whether to trigger an error",
                    default=False,
                )

            class Output(BlockSchemaOutput):
                result: int = SchemaField(description="Result")
                error_message: Optional[str] = SchemaField(
                    description="Error if any", default=None
                )

            def __init__(self):
                super().__init__(
                    id="error-handling-block",
                    description="Block with error handling",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=ErrorHandlingBlock.Input,
                    output_schema=ErrorHandlingBlock.Output,
                )

            async def run(self, input_data: Input, **kwargs) -> BlockOutput:
                if input_data.should_error:
                    raise ValueError("Intentional error triggered")

                if input_data.value < 0:
                    yield "error_message", "Value must be non-negative"
                    yield "result", 0
                else:
                    yield "result", input_data.value * 2
                    yield "error_message", None

        # Test normal operation
        block = ErrorHandlingBlock()
        outputs = {}
        async for name, value in block.run(
            ErrorHandlingBlock.Input(value=5, should_error=False)
        ):
            outputs[name] = value

        assert outputs["result"] == 10
        assert outputs["error_message"] is None

        # Test with negative value
        outputs = {}
        async for name, value in block.run(
            ErrorHandlingBlock.Input(value=-5, should_error=False)
        ):
            outputs[name] = value

        assert outputs["result"] == 0
        assert outputs["error_message"] == "Value must be non-negative"

        # Test with error
        with pytest.raises(ValueError, match="Intentional error triggered"):
            async for _ in block.run(
                ErrorHandlingBlock.Input(value=5, should_error=True)
            ):
                pass