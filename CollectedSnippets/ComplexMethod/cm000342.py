async def test_webhook_event_processing_block(self):
        """Test a block that processes webhook events."""

        class WebhookEventBlock(Block):
            """Block that processes webhook events."""

            class Input(BlockSchemaInput):
                event_type: str = SchemaField(description="Type of webhook event")
                payload: dict = SchemaField(description="Webhook payload")
                verify_signature: bool = SchemaField(
                    description="Whether to verify webhook signature",
                    default=True,
                )

            class Output(BlockSchemaOutput):
                processed: bool = SchemaField(description="Event was processed")
                event_summary: str = SchemaField(description="Summary of event")
                action_required: bool = SchemaField(description="Action required")

            def __init__(self):
                super().__init__(
                    id="webhook-event-processor",
                    description="Processes incoming webhook events",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=WebhookEventBlock.Input,
                    output_schema=WebhookEventBlock.Output,
                )

            async def run(self, input_data: Input, **kwargs) -> BlockOutput:
                # Process based on event type
                event_type = input_data.event_type
                payload = input_data.payload

                if event_type == "created":
                    summary = f"New item created: {payload.get('id', 'unknown')}"
                    action_required = True
                elif event_type == "updated":
                    summary = f"Item updated: {payload.get('id', 'unknown')}"
                    action_required = False
                elif event_type == "deleted":
                    summary = f"Item deleted: {payload.get('id', 'unknown')}"
                    action_required = True
                else:
                    summary = f"Unknown event: {event_type}"
                    action_required = False

                yield "processed", True
                yield "event_summary", summary
                yield "action_required", action_required

        # Test the block with different events
        block = WebhookEventBlock()

        # Test created event
        outputs = {}
        async for name, value in block.run(
            WebhookEventBlock.Input(
                event_type="created",
                payload={"id": "123", "name": "Test Item"},
            )
        ):
            outputs[name] = value

        assert outputs["processed"] is True
        assert "New item created: 123" in outputs["event_summary"]
        assert outputs["action_required"] is True

        # Test updated event
        outputs = {}
        async for name, value in block.run(
            WebhookEventBlock.Input(
                event_type="updated",
                payload={"id": "456", "changes": ["name", "status"]},
            )
        ):
            outputs[name] = value

        assert outputs["processed"] is True
        assert "Item updated: 456" in outputs["event_summary"]
        assert outputs["action_required"] is False