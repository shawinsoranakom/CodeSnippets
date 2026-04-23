def __call__(
        self,
        text: str | list[str] | list[dict],
        images: str | list[str] | list[list[str]] | ImageInput | None = None,
        videos: str | list[str] | VideoInput | None = None,
        audio: str | list[str] | AudioInput | None = None,
        **kwargs,
    ) -> list[dict[str, Any]] | list[list[dict[str, Any]]]:
        """
        Generate a text given text and optionally multimodal data passed as inputs.

        Args:
            text (`str`, `list[str]`, `list[dict]`):
                The text to be used for generation. If a list of strings is passed, the length of the list should be
                the same as the number of images. Text can also follow the chat format: a list of dictionaries where
                each dictionary represents a message in a conversation. Each dictionary should have two keys: 'role'
                and 'content'. 'role' should be one of 'user', 'system' or 'assistant'. 'content' should be a list of
                dictionary containing the text of the message and the type of the message.
            images (`str`, `list[str]`, `ImageInput`):
                The pipeline handles three types of images:

                - A string containing a HTTP(s) link pointing to an image
                - A string containing a local path to an image
                - An image loaded in PIL directly

                The pipeline accepts either a single image or a batch of images. Finally, this pipeline also supports
                the chat format (see `text`) containing images and text in this argument.
            videos (`str`, `list[str]`, `VideoInput`):
                The pipeline handles three types of videos:

                - A string containing a HTTP(s) link pointing to a video
                - A string containing a local path to a video
                - A video loaded and decoded to array format

                The pipeline accepts either a single video or a batch of videos. Finally, this pipeline also supports
                the chat format (see `text`) containing videos and text in this argument.
            audio (`str`, `list[str]`, `AudioInput`):
                The pipeline handles three types of audios:

                - A string containing a HTTP(s) link pointing to an audio
                - A string containing a local path to an audio
                - An audio loaded in PIL directly

                The pipeline accepts either a single audios or a batch of audios. Finally, this pipeline also supports
                the chat format (see `text`) containing audios and text in this argument.
            return_tensors (`bool`, *optional*, defaults to `False`):
                Returns the tensors of predictions (as token indices) in the outputs. If set to
                `True`, the decoded text is not returned.
            return_text (`bool`, *optional*):
                Returns the decoded texts in the outputs.
            return_full_text (`bool`, *optional*, defaults to `True`):
                If set to `False` only added text is returned, otherwise the full text is returned. Cannot be
                specified at the same time as `return_text`.
            clean_up_tokenization_spaces (`bool`, *optional*, defaults to `True`):
                Whether or not to clean up the potential extra spaces in the text output.
            continue_final_message( `bool`, *optional*): This indicates that you want the model to continue the
                last message in the input chat rather than starting a new one, allowing you to "prefill" its response.
                By default this is `True` when the final message in the input chat has the `assistant` role and
                `False` otherwise, but you can manually override that behaviour by setting this flag.

        Return:
            A list or a list of list of `dict`: Each result comes as a dictionary with the following key (cannot
            return a combination of both `generated_text` and `generated_token_ids`):

            - **generated_text** (`str`, present when `return_text=True` and `generation_mode="text"`) -- The generated text.
            - **generated_audio** (`np.ndarray`, present when `generation_mode="audio"`) -- The generated audio.
            - **generated_image** (`PIL.Image.Image`, present when `generation_mode="image"`) -- The generated image.
            - **generated_token_ids** (`torch.Tensor`, present when `return_tensors=True` and `generation_mode="text"`) -- The token
                ids of the generated text.
            - **input_text** (`str`) -- The input text.
        """
        if images is None and text is None:
            raise ValueError("You must at least provide either text or images.")

        if isinstance(text, (list, tuple, KeyDataset)) and isinstance(text[0], (list, tuple, dict)):
            # We have one or more prompts in list-of-dicts format, so this is chat mode
            if isinstance(text[0], dict) and "role" in text[0]:
                return super().__call__(Chat(text), **kwargs)
            elif isinstance(text[0], (list, tuple)) and isinstance(text[0][0], dict) and "role" in text[0][0]:
                chats = [Chat(chat) for chat in text]  # 🐈 🐈 🐈
                return super().__call__(chats, **kwargs)

        if text is not None and not (isinstance(text, str) or (isinstance(text, list) and isinstance(text[0], str))):
            """
            Supports the following format
            - {"text": text, "image": image, "video": video, "audio": audio}
            - [{"text": text, "image": image, "video": video, "audio": audio}]
            - Generator and datasets
            This is a common pattern in other multimodal pipelines, so we support it here as well.
            """
            return super().__call__(text, **kwargs)

        # encourage the user to use the chat format if supported
        if getattr(self.processor, "chat_template", None) is not None:
            logger.warning_once(
                "The input data was not formatted as a chat with dicts containing 'role' and 'content' keys, even "
                "though this model supports chat. Consider using the chat format for better results. For more "
                "information, see https://huggingface.co/docs/transformers/en/chat_templating"
            )

        return super().__call__({"text": text, "images": images, "video": videos, "audio": audio}, **kwargs)