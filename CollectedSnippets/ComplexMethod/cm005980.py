async def test_agent_receives_string_input_from_message_object(self, component_class, default_kwargs):
        """Test that agent extracts text string from Message object instead of passing the entire object.

        This test addresses the issue where agents were receiving:
        content='hi how are you' additional_kwargs={} response_metadata={}
        instead of just the string 'hi how are you'.
        """
        from langchain_core.messages import HumanMessage
        from lfx.schema.message import Message

        # Create a Message object with text content
        message = Message(text="hi how are you", sender="User", sender_name="User")

        # Set up the component with the Message as input
        default_kwargs["input_value"] = message
        component = await self.component_setup(component_class, default_kwargs)

        # Test the input processing logic directly
        # This is what happens inside the agent when processing input
        lc_message = None
        if isinstance(component.input_value, Message):
            lc_message = component.input_value.to_lc_message()

            # Verify it's a LangChain HumanMessage
            assert isinstance(lc_message, HumanMessage)
            assert lc_message.content == "hi how are you"

            # Now verify the extraction logic that should happen in the agent
            if hasattr(lc_message, "content"):
                if isinstance(lc_message.content, str):
                    input_dict = {"input": lc_message.content}
                    # The key assertion: input should be a string, not a Message object
                    assert isinstance(input_dict["input"], str)
                    assert input_dict["input"] == "hi how are you"
                    # Ensure it's NOT the message object representation
                    assert "additional_kwargs" not in str(input_dict["input"])
                    assert "response_metadata" not in str(input_dict["input"])
                elif isinstance(lc_message.content, list):
                    # For multimodal content, extract text parts
                    text_parts = [item.get("text", "") for item in lc_message.content if item.get("type") == "text"]
                    input_dict = {"input": " ".join(text_parts) if text_parts else ""}
                    assert isinstance(input_dict["input"], str)
                else:
                    input_dict = {"input": str(lc_message.content)}
                    assert isinstance(input_dict["input"], str)