def test_multimodal_parts(self):
        payload = ResponsesRequest(
            input = [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Describe this:"},
                        {
                            "type": "input_image",
                            "image_url": "data:image/png;base64,abc",
                        },
                    ],
                },
            ],
        )
        msgs = _normalise_responses_input(payload)
        assert len(msgs) == 1
        content = msgs[0].content
        assert isinstance(content, list)
        assert len(content) == 2
        assert isinstance(content[0], TextContentPart)
        assert content[0].text == "Describe this:"
        assert isinstance(content[1], ImageContentPart)
        assert content[1].image_url.url == "data:image/png;base64,abc"