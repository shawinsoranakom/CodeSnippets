def test_commentary_with_no_recipient_creates_message(self):
        """Test that commentary with recipient=None (preambles) creates message items.

        Per Harmony format, preambles are intended to be shown to end-users,
        unlike analysis channel content which is hidden reasoning.
        See: https://cookbook.openai.com/articles/openai-harmony
        """
        message = Message.from_role_and_content(
            Role.ASSISTANT, "I will now search for the weather information."
        )
        message = message.with_channel("commentary")
        # recipient is None by default, representing a preamble

        output_items = harmony_to_response_output(message)

        assert len(output_items) == 1
        assert isinstance(output_items[0], ResponseOutputMessage)
        assert output_items[0].type == "message"
        assert output_items[0].role == "assistant"
        assert output_items[0].status == "completed"
        assert len(output_items[0].content) == 1
        assert output_items[0].content[0].type == "output_text"
        assert (
            output_items[0].content[0].text
            == "I will now search for the weather information."
        )