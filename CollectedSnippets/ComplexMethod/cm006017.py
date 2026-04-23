async def test_message_response(self, component_class, default_kwargs):
        """Test that the message_response method returns a valid Message object."""
        component = component_class(**default_kwargs)
        message = await component.message_response()

        assert isinstance(message, Message)
        assert message.text == default_kwargs["input_value"]
        assert message.sender == default_kwargs["sender"]
        assert message.sender_name == default_kwargs["sender_name"]
        assert message.session_id == default_kwargs["session_id"]
        assert message.files == default_kwargs["files"]
        assert message.properties.model_dump() == {
            "background_color": None,
            "text_color": None,
            "icon": None,
            "positive_feedback": None,
            "edited": False,
            "source": {"id": None, "display_name": None, "source": None},
            "allow_markdown": False,
            "state": "complete",
            "targets": [],
            "usage": None,
            "build_duration": None,
        }