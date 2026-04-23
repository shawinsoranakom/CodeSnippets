def test_normalize_message_content_function(self):
        """Test the normalize_message_content helper function in ALTK agent."""
        from lfx.base.agents.altk_base_agent import normalize_message_content
        from lfx.schema.data import Data

        # Test with User message (list format)
        user_data = Data(data={"text": "user message", "sender": "User"})
        user_message = user_data.to_lc_message()

        normalized_user_text = normalize_message_content(user_message)
        assert normalized_user_text == "user message"

        # Test with Assistant message (string format)
        assistant_data = Data(data={"text": "assistant message", "sender": "Assistant"})
        assistant_message = assistant_data.to_lc_message()

        normalized_assistant_text = normalize_message_content(assistant_message)
        assert normalized_assistant_text == "assistant message"

        # Both should normalize to the same format
        assert isinstance(normalized_user_text, str)
        assert isinstance(normalized_assistant_text, str)

        # Test edge case: empty list content
        from langchain_core.messages import HumanMessage

        empty_message = HumanMessage(content=[])
        normalized_empty = normalize_message_content(empty_message)
        assert normalized_empty == ""

        # Test edge case: non-text content in list (image-only)
        complex_message = HumanMessage(content=[{"type": "image", "url": "test.jpg"}])
        normalized_complex = normalize_message_content(complex_message)
        assert normalized_complex == ""  # Should return empty string when no text found

        # Test edge case: mixed content with text
        mixed_message = HumanMessage(
            content=[
                {"type": "image", "url": "test.jpg"},
                {"type": "text", "text": "check this image"},
            ]
        )
        normalized_mixed = normalize_message_content(mixed_message)
        assert normalized_mixed == "check this image"