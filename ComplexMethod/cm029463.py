async def test_image_mode_create_with_image_generation_disabled(self) -> None:
        params: Dict[str, Any] = {
            "prompt": {"text": "", "images": [self.TEST_IMAGE_URL]},
            "generationType": "create",
        }

        with patch("prompts.system_prompt.SYSTEM_PROMPT", new=self.MOCK_SYSTEM_PROMPT):
            messages = await build_prompt_messages(
                stack=self.TEST_STACK,
                input_mode="image",
                generation_type=params["generationType"],
                prompt=params["prompt"],
                history=[],
                image_generation_enabled=False,
            )

        system_content = messages[0].get("content")
        assert isinstance(system_content, str)
        assert system_content == self.MOCK_SYSTEM_PROMPT

        user_content = messages[1].get("content")
        assert isinstance(user_content, list)
        text_part = next(
            (
                part
                for part in user_content
                if isinstance(part, dict) and part.get("type") == "text"
            ),
            None,
        )
        assert isinstance(text_part, dict)
        user_text = text_part.get("text")
        assert isinstance(user_text, str)
        assert "Image generation is disabled for this request. Do not call generate_images." in user_text