async def test_update_bootstraps_from_file_state_when_history_is_empty(self) -> None:
        """Update should synthesize a user message from fileState + prompt when history is empty."""
        ref_image_url: str = "data:image/png;base64,ref_image"
        params: Dict[str, Any] = {
            "generationType": "update",
            "prompt": {"text": "Make the header blue", "images": [ref_image_url], "videos": []},
            "history": [],
            "fileState": {
                "path": "index.html",
                "content": "<html>Original imported code</html>",
            },
        }

        with patch(
            "prompts.system_prompt.SYSTEM_PROMPT",
            new=self.MOCK_SYSTEM_PROMPT,
        ):
            messages = await build_prompt_messages(
                stack=self.TEST_STACK,
                input_mode="image",
                generation_type=params["generationType"],
                prompt=params["prompt"],
                history=params["history"],
                file_state=params["fileState"],
            )

            expected: ExpectedResult = {
                "messages": [
                    {
                        "role": "system",
                        "content": self.MOCK_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": ref_image_url,
                                    "detail": "high",
                                },
                            },
                            {
                                "type": "text",
                                "text": "<CONTAINS:<current_file path=\"index.html\">>",
                            },
                        ],
                    },
                ],
            }

            actual: ExpectedResult = {"messages": messages}
            assert_structure_match(actual, expected)
            user_content = messages[1].get("content")
            assert isinstance(user_content, list)
            text_part = next(
                (part for part in user_content if isinstance(part, dict) and part.get("type") == "text"),
                None,
            )
            assert isinstance(text_part, dict)
            synthesized_text = text_part.get("text", "")
            assert isinstance(synthesized_text, str)
            assert f"Selected stack: {self.TEST_STACK}." in synthesized_text
            assert "<html>Original imported code</html>" in synthesized_text
            assert "<change_request>" in synthesized_text
            assert "Make the header blue" in synthesized_text