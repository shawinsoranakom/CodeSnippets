def apply_chat_template(  # type: ignore[override]
        self,
        conversation: list[dict[str, str]] | list[list[dict[str, str]]],
        tools: list[dict | Callable] | None = None,
        add_generation_prompt: bool = False,
        continue_final_message: bool = False,
        tokenize: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool = False,
        max_length: int | None = None,
        return_tensors: str | TensorType | None = None,
        return_dict: bool = True,
        reasoning_effort: ReasoningEffort | None = None,
        **kwargs,
    ) -> str | list[int] | list[str] | list[list[int]] | BatchEncoding:
        """
        Converts a list of dictionaries with `"role"` and `"content"` keys to a list of token
        ids.

        Args:
            conversation (Union[List[Dict[str, str]], List[List[Dict[str, str]]]]): A list of dicts
                with "role" and "content" keys, representing the chat history so far.
            tools (`List[Union[Dict, Callable]]`, *optional*):
                A list of tools (callable functions) that will be accessible to the model. If the template does not
                support function calling, this argument will have no effect. Each tool should be passed as a JSON Schema,
                giving the name, description and argument types for the tool. See our
                [chat templating guide](https://huggingface.co/docs/transformers/main/en/chat_templating#automated-function-conversion-for-tool-use)
                for more information.
            add_generation_prompt (`bool`, *optional*):
                This argument is a no-op for `MistralCommonBackend`. However, it cannot be used at the same time as `continue_final_message` to keep the API consistent.
                If any conversation ends with an assistant message, it will raise an error. In such cases, use `continue_final_message` instead.
            continue_final_message (bool, *optional*):
                If this is set, the chat will be formatted so that the final
                message in the chat is open-ended, without any EOS tokens. The model will continue this message
                rather than starting a new one. This allows you to "prefill" part of
                the model's response for it. Cannot be used at the same time as `add_generation_prompt`.
            tokenize (`bool`, defaults to `True`):
                Whether to tokenize the output. If `False`, the output will be a string.
            padding (`bool`, `str` or [`~utils.PaddingStrategy`], *optional*, defaults to `False`):
                 Select a strategy to pad the returned sequences (according to the model's padding side and padding
                 index) among:

                - `True` or `'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
                  sequence if provided).
                - `'max_length'`: Pad to a maximum length specified with the argument `max_length` or to the maximum
                  acceptable input length for the model if that argument is not provided.
                - `False` or `'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of different
                  lengths).
            truncation (`bool`, defaults to `False`):
                Whether to truncate sequences at the maximum length. Has no effect if tokenize is `False`.
            max_length (`int`, *optional*):
                Maximum length (in tokens) to use for padding or truncation. Has no effect if tokenize is `False`. If
                not specified, the tokenizer's `max_length` attribute will be used as a default.
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors of a particular framework. Has no effect if tokenize is `False`. Acceptable
                values are:
                - `'pt'`: Return PyTorch `torch.Tensor` objects.
            return_dict (`bool`, defaults to `False`):
                Whether to return a dictionary with named outputs. Has no effect if tokenize is `False`.
                If at least one conversation contains an image, its pixel values will be returned in the `pixel_values` key and image sizes in the `image_sizes` key.
            reasoning_effort (`ReasoningEffort`, *optional*):
                The reasoning effort to use for the chat completion for models that support it. Possible values are:
                - `ReasoningEffort.none`: The model will not reason.
                - `ReasoningEffort.high`: The model will use a reasoning approach.
                If not specified, the default reasoning effort will be used.

            kwargs (additional keyword arguments, *optional*):
                Not supported by `MistralCommonBackend.apply_chat_template`.
                Will raise an error if used.

        Returns:
            `Union[str, list[int], list[str], list[list[int]], BatchEncoding]`: The tokenized chat so far, including control tokens. This output is ready to pass to the model, either directly or via methods like `generate()`.
        """
        if kwargs:
            raise ValueError(
                f"Kwargs {list(kwargs.keys())} are not supported by `MistralCommonBackend.apply_chat_template`."
            )
        if not isinstance(truncation, bool):
            raise TypeError("`truncation` must be a boolean for `apply_chat_template` method.")

        if add_generation_prompt and continue_final_message:
            raise ValueError("Cannot use both `add_generation_prompt` and `continue_final_message`.")

        if isinstance(conversation, (list, tuple)) and (
            isinstance(conversation[0], (list, tuple)) or hasattr(conversation[0], "messages")
        ):
            conversations = conversation
            is_batched = True
        else:
            conversations = [conversation]
            is_batched = False

        if add_generation_prompt:
            for conversation in conversations:
                last_message = conversation[-1]
                if last_message.get("role") == "assistant":
                    raise ValueError(
                        "The last message in the conversation is already an assistant message. Consider using `continue_final_message` instead."
                    )

        def _maybe_adapt_message(message: dict[str, Any]) -> None:
            """Adapt message to `mistral-common` format and leave validation to `mistral-common`."""
            if not isinstance(message, dict):
                return message
            maybe_list_content: str | list[dict[str, str | dict[str, Any]]] | None = message.get("content")
            if not maybe_list_content or isinstance(maybe_list_content, str):
                return message

            normalized_content: list[dict[str, str | dict[str, Any]]] = []
            message = message.copy()
            for content in maybe_list_content:
                content_type = content.get("type", None)
                if not content_type:
                    continue
                elif content_type == "image":
                    maybe_url: str | None = content.get("url")
                    maybe_path: str | None = content.get("path")
                    maybe_base64: str | None = content.get("base64")
                    if maybe_url:
                        image_content = maybe_url
                    elif maybe_path:
                        if not maybe_path.startswith("file://"):
                            maybe_path = Path(maybe_path).resolve().as_uri()
                        image_content = maybe_path
                    elif maybe_base64:
                        if not maybe_base64.startswith("data:image"):
                            maybe_base64 = "data:image/unk;base64," + maybe_base64
                        image_content = maybe_base64
                    else:
                        raise ValueError("Image content must be specified.")
                    normalized_content.append({"type": "image_url", "image_url": {"url": image_content}})
                elif content_type == "audio":
                    maybe_url: str | None = content.get("url")
                    maybe_path: str | None = content.get("path")
                    maybe_base64: str | None = content.get("base64")
                    if maybe_url or maybe_path:
                        audio_data = load_audio_as(maybe_url or maybe_path, return_format="dict", force_mono=True)
                        normalized_content.append({"type": "input_audio", "input_audio": audio_data})
                        continue
                    if not maybe_base64:
                        raise ValueError("Audio content must be specified.")
                    normalized_content.append({"type": "audio_url", "audio_url": {"url": maybe_base64}})
                else:
                    normalized_content.append(content)
            message["content"] = normalized_content
            return message

        outputs = []
        images: list[np.ndarray] = []
        audios: list[np.ndarray] = []

        for conversation in conversations:
            messages: list[dict[str, str | list[dict[str, str | dict[str, Any]]]]] = []
            for message in conversation:
                message = _maybe_adapt_message(message)
                messages.append(message)

            chat_request = ChatCompletionRequest.from_openai(
                messages=messages,
                tools=tools,
                continue_final_message=continue_final_message,
                reasoning_effort=reasoning_effort,
            )

            tokenized_request = self.tokenizer.encode_chat_completion(chat_request)
            if tokenize:
                outputs.append(tokenized_request.tokens)
            else:
                outputs.append(tokenized_request.text)
            images.extend(tokenized_request.images)
            audios.extend([el.audio_array for el in tokenized_request.audios])

        if not is_batched:
            outputs = outputs[0]

        if tokenize:
            out = self(
                outputs,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                add_special_tokens=False,
                return_tensors=return_tensors,
            )
            if return_dict:
                if images:
                    pixel_values: list[np.ndarray] | np.ndarray | torch.Tensor
                    if return_tensors == "pt":
                        if not is_torch_available():
                            raise ImportError(
                                "Unable to convert output to PyTorch tensors format, PyTorch is not installed."
                            )

                        pixel_values = torch.from_numpy(np.stack(images))
                    elif return_tensors == "np":
                        pixel_values = np.array(images)
                    elif return_tensors is None:
                        pixel_values = images
                    else:
                        raise ValueError(f"Unsupported return_tensors type: {return_tensors}")
                    out.data["pixel_values"] = pixel_values
                if images:
                    out.data["image_sizes"] = self._get_image_sizes_for_tensor(images, return_tensors)
                if audios:
                    if return_tensors is not None:
                        raise NotImplementedError(
                            "When passing audio content in apply_chat_template, `return_tensors` must be None since we cannot batch the audio inputs. The returned audio will be a list of numpy arrays."
                        )
                    # Transformers convention is audio for plural audio (audio does not take a "s")
                    out.data["audio"] = audios
                return out
            else:
                return out["input_ids"]

        else:
            logger.warning(
                "`MistralCommonBackend.apply_chat_template(..., tokenize=False)` is unsafe and may lead to unexpected behavior."
                " Please consider using `tokenize=True` instead and don't encode the output manually."
            )
            return outputs