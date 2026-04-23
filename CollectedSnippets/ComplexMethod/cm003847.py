def apply_chat_template(
        self,
        conversation: list[dict[str, str]] | list[list[dict[str, str]]],
        chat_template: str | None = None,
        processor_kwargs: dict | None = None,
        **kwargs,
    ) -> str:
        """
        Similar to the `apply_chat_template` method on tokenizers, this method applies a Jinja template to input
        conversations to turn them into a single tokenizable string.

        The input is expected to be in the following format, where each message content is a list consisting of text and
        optionally image or video inputs. One can also provide an image, video, URL or local path which will be used to form
        `pixel_values` when `return_dict=True`. If not provided, one will get only the formatted text, optionally tokenized text.

        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "url": "https://www.ilankelman.org/stopsigns/australia.jpg"},
                    {"type": "text", "text": "Please describe this image in detail."},
                ],
            },
        ]

        Args:
            conversation (`Union[list[Dict, [str, str]], list[list[dict[str, str]]]]`):
                The conversation to format.
            chat_template (`Optional[str]`, *optional*):
                The Jinja template to use for formatting the conversation. If not provided, the tokenizer's
                chat template is used.
        """
        if isinstance(conversation, (list, tuple)) and (
            isinstance(conversation[0], (list, tuple)) or hasattr(conversation[0], "content")
        ):
            conversations = conversation
        else:
            conversations = [conversation]

        has_video = any(
            (isinstance(content, dict) and content["type"] == "video")
            for conversation in conversations
            for message in conversation
            for content in (message.get("content") or [])
        )
        if chat_template is None and has_video:
            # re-assign to the correct default template for BC, if user is not requesting their own template
            chat_template = DEFAULT_CHAT_TEMPLATE

        # Users might be passing processor kwargs simply as `**kwargs`
        if processor_kwargs:
            processor_kwargs.setdefault("num_frames", self.video_processor.num_frames)
            processor_kwargs.setdefault("fps", self.video_processor.fps)
        else:
            kwargs.setdefault("num_frames", self.video_processor.num_frames)
            kwargs.setdefault("fps", self.video_processor.fps)

        return super().apply_chat_template(conversation, chat_template, processor_kwargs=processor_kwargs, **kwargs)