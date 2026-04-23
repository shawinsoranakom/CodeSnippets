def test_tool_result_with_text_and_image(self):
        """Mixed text+image tool_result: text in tool msg, image in user
        msg."""
        request = self._make_tool_result_request(
            [
                {"type": "text", "text": "Here is the screenshot"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": "QUFB",
                    },
                },
            ]
        )
        result = _convert(request)

        tool_msg = [m for m in result.messages if m["role"] == "tool"]
        assert len(tool_msg) == 1
        assert tool_msg[0]["content"] == "Here is the screenshot"

        follow_up = [
            m
            for m in result.messages
            if m["role"] == "user" and isinstance(m.get("content"), list)
        ]
        assert len(follow_up) == 1
        assert follow_up[0]["content"][0]["image_url"]["url"] == (
            "data:image/jpeg;base64,QUFB"
        )