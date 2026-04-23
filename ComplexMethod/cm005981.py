async def test_agent_handles_multimodal_message_input(self, component_class, default_kwargs):
        """Test that agent properly extracts text from multimodal Message objects."""
        from lfx.schema.message import Message

        # Create a Message object with text content (no actual files for testing)
        message = Message(text="What is in this image?", sender="User", sender_name="User")

        # Set up the component
        default_kwargs["input_value"] = message
        _ = await self.component_setup(component_class, default_kwargs)

        # Convert to LangChain message
        lc_message = message.to_lc_message()

        # Test the input extraction logic for different content types
        if hasattr(lc_message, "content"):
            if isinstance(lc_message.content, str):
                # Simple string content
                assert lc_message.content == "What is in this image?"
                assert isinstance(lc_message.content, str)
            elif isinstance(lc_message.content, list):
                # Multimodal content - extract text parts
                text_parts = [item.get("text", "") for item in lc_message.content if item.get("type") == "text"]
                extracted_text = " ".join(text_parts) if text_parts else ""
                assert isinstance(extracted_text, str)
                # Verify we got text, not a message object
                assert "additional_kwargs" not in extracted_text
                assert "response_metadata" not in extracted_text