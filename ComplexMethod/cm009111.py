def get_num_tokens_from_messages(
        self,
        messages: Sequence[BaseMessage],
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool] | None = None,
        *,
        allow_fetching_images: bool = True,
    ) -> int:
        """Calculate num tokens for `gpt-3.5-turbo` and `gpt-4` with `tiktoken` package.

        !!! warning
            You must have the `pillow` installed if you want to count image tokens if
            you are specifying the image as a base64 string, and you must have both
            `pillow` and `httpx` installed if you are specifying the image as a URL. If
            these aren't installed image inputs will be ignored in token counting.

        [OpenAI reference](https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb).

        Args:
            messages: The message inputs to tokenize.
            tools: If provided, sequence of `dict`, `BaseModel`, function, or `BaseTool`
                to be converted to tool schemas.
            allow_fetching_images: Whether to allow fetching images for token counting.
        """
        # TODO: Count bound tools as part of input.
        if tools is not None:
            warnings.warn(
                "Counting tokens in tool schemas is not yet supported. Ignoring tools."
            )
        if sys.version_info[1] <= 7:
            return super().get_num_tokens_from_messages(messages)
        model, encoding = self._get_encoding_model()
        if model.startswith("gpt-3.5-turbo-0301"):
            # every message follows <im_start>{role/name}\n{content}<im_end>\n
            tokens_per_message = 4
            # if there's a name, the role is omitted
            tokens_per_name = -1
        elif model.startswith(("gpt-3.5-turbo", "gpt-4", "gpt-5")):
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            msg = (
                f"get_num_tokens_from_messages() is not presently implemented "
                f"for model {model}. See "
                "https://platform.openai.com/docs/guides/text-generation/managing-tokens"
                " for information on how messages are converted to tokens."
            )
            raise NotImplementedError(msg)
        num_tokens = 0
        messages_dict = [_convert_message_to_dict(m) for m in messages]
        for message in messages_dict:
            num_tokens += tokens_per_message
            for key, value in message.items():
                # This is an inferred approximation. OpenAI does not document how to
                # count tool message tokens.
                if key == "tool_call_id":
                    num_tokens += 3
                    continue
                if isinstance(value, list):
                    # content or tool calls
                    for val in value:
                        if isinstance(val, str) or val["type"] == "text":
                            text = val["text"] if isinstance(val, dict) else val
                            num_tokens += len(encoding.encode(text))
                        elif val["type"] == "image_url":
                            if val["image_url"].get("detail") == "low":
                                num_tokens += 85
                            elif allow_fetching_images:
                                image_size = _url_to_size(val["image_url"]["url"])
                                if not image_size:
                                    continue
                                num_tokens += _count_image_tokens(*image_size)
                            else:
                                pass
                        # Tool/function call token counting is not documented by OpenAI.
                        # This is an approximation.
                        elif val["type"] == "function":
                            num_tokens += len(
                                encoding.encode(val["function"]["arguments"])
                            )
                            num_tokens += len(encoding.encode(val["function"]["name"]))
                        elif val["type"] == "file":
                            warnings.warn(
                                "Token counts for file inputs are not supported. "
                                "Ignoring file inputs."
                            )
                        else:
                            msg = f"Unrecognized content block type\n\n{val}"
                            raise ValueError(msg)
                elif not value:
                    continue
                else:
                    # Cast str(value) in case the message value is not a string
                    # This occurs with function messages
                    num_tokens += len(encoding.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name
        # every reply is primed with <im_start>assistant
        num_tokens += 3
        return num_tokens