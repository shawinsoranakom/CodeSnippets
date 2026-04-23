def test_data_to_message_with_multiple_images(self, sample_image, tmp_path):
        """Test conversion of Data to Message with multiple images."""
        # Create a second image
        second_image = tmp_path / "second_image.png"
        second_image.write_bytes(sample_image.read_bytes())

        data = Data(
            data={
                "text": "Multiple images",
                "sender": MESSAGE_SENDER_USER,
                "files": [str(sample_image), str(second_image)],
            }
        )
        message = data.to_lc_message()

        assert isinstance(message, HumanMessage)
        assert isinstance(message.content, list)
        expected_content_len = 3  # text + 2 images
        assert len(message.content) == expected_content_len

        # Check text content
        text_content = message.content[0]
        assert text_content["type"] == "text"

        # Check both images
        assert message.content[1]["type"] == "image_url"
        assert "image_url" in message.content[1]
        assert "url" in message.content[1]["image_url"]
        assert message.content[1]["image_url"]["url"].startswith("data:image/png;base64,")

        assert message.content[2]["type"] == "image_url"
        assert "image_url" in message.content[2]
        assert "url" in message.content[2]["image_url"]
        assert message.content[2]["image_url"]["url"].startswith("data:image/png;base64,")