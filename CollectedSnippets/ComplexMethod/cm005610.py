def __call__(
        self,
        images: Union[
            str, list[str], list[list[str]], "Image.Image", list["Image.Image"], list[list["Image.Image"]], list[dict]
        ]
        | None = None,
        text: str | list[str] | list[dict] | None = None,
        **kwargs,
    ) -> list[dict[str, Any]] | list[list[dict[str, Any]]]:
        """
        Generate a text given text and the image(s) passed as inputs.

        Args:
            images (`str`, `list[str]`, `PIL.Image, `list[PIL.Image]`, `list[dict[str, Union[str, PIL.Image]]]`):
                The pipeline handles three types of images:

                - A string containing a HTTP(s) link pointing to an image
                - A string containing a local path to an image
                - An image loaded in PIL directly

                The pipeline accepts either a single image or a batch of images. Finally, this pipeline also supports
                the chat format (see `text`) containing images and text in this argument.
            text (str, list[str], `list[dict[str, Union[str, PIL.Image]]]`):
                The text to be used for generation. If a list of strings is passed, the length of the list should be
                the same as the number of images. Text can also follow the chat format: a list of dictionaries where
                each dictionary represents a message in a conversation. Each dictionary should have two keys: 'role'
                and 'content'. 'role' should be one of 'user', 'system' or 'assistant'. 'content' should be a list of
                dictionary containing the text of the message and the type of the message. The type of the message
                can be either 'text' or 'image'. If the type is 'image', no text is needed.
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

            - **generated_text** (`str`, present when `return_text=True`) -- The generated text.
            - **generated_token_ids** (`torch.Tensor`, present when `return_tensors=True`) -- The token
                ids of the generated text.
            - **input_text** (`str`) -- The input text.
        """
        if images is None and text is None:
            raise ValueError("You must at least provide either text or images.")

        def _is_chat(arg):
            return isinstance(arg, (list, tuple, KeyDataset)) and isinstance(arg[0], (list, tuple, dict))

        if _is_chat(text):
            if images is not None:
                raise ValueError(
                    "Invalid input: you passed `chat` and `images` as separate input arguments. "
                    "Images must be placed inside the chat message's `content`. For example, "
                    "'content': ["
                    "      {'type': 'image', 'url': 'image_url'}, {'type': 'text', 'text': 'Describe the image.'}}"
                    "]"
                )
            # We have one or more prompts in list-of-dicts format, so this is chat mode
            if isinstance(text[0], dict):
                return super().__call__(Chat(text), **kwargs)
            else:
                chats = [Chat(chat) for chat in text]  # 🐈 🐈 🐈
                return super().__call__(chats, **kwargs)

        # Same as above, but the `images` argument contains the chat. This can happen e.g. is the user only passes a
        # chat as a positional argument.
        elif text is None and _is_chat(images):
            # We have one or more prompts in list-of-dicts format, so this is chat mode
            if isinstance(images[0], dict):
                return super().__call__(Chat(images), **kwargs)
            else:
                chats = [Chat(image) for image in images]  # 🐈 🐈 🐈
                return super().__call__(chats, **kwargs)

        elif images is not None and text is None and not valid_images(images):
            """
            Supports the following format
            - {"image": image, "text": text}
            - [{"image": image, "text": text}]
            - Generator and datasets
            This is a common pattern in other multimodal pipelines, so we support it here as well.
            """
            return super().__call__(images, **kwargs)

        # encourage the user to use the chat format if supported
        if getattr(self.processor, "chat_template", None) is not None:
            logger.warning_once(
                "The input data was not formatted as a chat with dicts containing 'role' and 'content' keys, even "
                "though this model supports chat. Consider using the chat format for better results. For more "
                "information, see https://huggingface.co/docs/transformers/en/chat_templating"
            )

        # support text only generation
        if images is None:
            return super().__call__(text, **kwargs)
        if text is None:
            raise ValueError("You must provide text for this pipeline.")

        return super().__call__({"images": images, "text": text}, **kwargs)