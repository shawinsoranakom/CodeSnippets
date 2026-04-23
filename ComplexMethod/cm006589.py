def test_data_to_message_with_image(self, sample_image):
        """Test conversion of Data to Message with text and image."""
        data = Data(data={"text": "Check out this image", "sender": MESSAGE_SENDER_USER, "files": [str(sample_image)]})
        message = data.to_lc_message()

        assert isinstance(message, HumanMessage)
        assert isinstance(message.content, list)
        expected_content_len = 2
        assert len(message.content) == expected_content_len

        # Check text content
        text_content = message.content[0]
        assert text_content == {"type": "text", "text": "Check out this image"}

        # Check image content
        assert message.content[1]["type"] == "image_url"
        assert "image_url" in message.content[1]
        assert "url" in message.content[1]["image_url"]
        assert message.content[1]["image_url"]["url"].startswith("data:image/png;base64,")