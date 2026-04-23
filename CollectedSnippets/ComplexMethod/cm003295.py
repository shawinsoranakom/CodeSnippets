def apply_chat_template(
        self,
        conversation: list[dict[str, str]] | list[list[dict[str, str]]],
        chat_template: str | None = None,
        tools: list[dict] | None = None,
        documents: list[dict[str, str]] | None = None,
        add_generation_prompt: bool = False,
        continue_final_message: bool = False,
        return_assistant_tokens_mask: bool = False,
        tokenize: bool = False,
        return_tensors: str | None = None,
        return_dict: bool = False,
        load_audio_from_video: bool = False,
        processor_kwargs: dict | None = None,
        **kwargs,
    ) -> str:
        """
        This method applies the model's chat completion template given a conversation. It relies on MistralCommonBackend's
        [`~MistralCommonBackend.apply_chat_template`] to prepare input ids to the model and on WhisperFeatureExtractor's
        [`~WhisperFeatureExtractor.__call__`] to prepare input features to the model.

        Note that audio is padded to the nearest 30-second multiple prior to mel feature extraction.

        A `conversation` is a list of messages, where each message is a dictionary with a `role` and a `content` field.
        For Voxtral, `role` can be `"user"` or `"assistant"`.
        The `content` field can be a string or a list of dictionaries with a `type` field. See example below.

        ```python
        from huggingface_hub import hf_hub_download
        from transformers.audio_utils import load_audio_as

        audio_url = "https://huggingface.co/datasets/hf-internal-testing/dummy-audio-samples/resolve/main/bcn_weather.mp3"
        audio_path = hf_hub_download(repo_id="hf-internal-testing/dummy-audio-samples", filename="bcn_weather.mp3", repo_type="dataset")
        audio_base64 = load_audio_as(audio_path, return_format="base64", force_mono=True)

        # audio + text
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "url": audio_url},
                    {"type": "audio", "path": audio_path},
                    {"type": "audio", "base64": audio_base64},
                    {"type": "text", "text": "How many audio do you hear?"},
                ],
            },
        ]

        processor = VoxtralProcessor.from_pretrained("mistralai/Voxtral-Mini-3B-2507")
        inputs = processor.apply_chat_template(conversation)
        ```

        Args:
            conversation (`Union[list[Dict, [str, str]], list[list[dict[str, str]]]]`):
                The conversation to format.
        """
        if continue_final_message:
            if add_generation_prompt:
                raise ValueError(
                    "continue_final_message and add_generation_prompt are not compatible. Use continue_final_message when you want the model to continue the final message, and add_generation_prompt when you want to add a header that will prompt it to start a new assistant message instead."
                )
            if return_assistant_tokens_mask:
                raise ValueError("continue_final_message is not compatible with return_assistant_tokens_mask.")

        if isinstance(conversation, (list, tuple)) and (
            isinstance(conversation[0], (list, tuple)) or hasattr(conversation[0], "content")
        ):
            is_batched = True
            conversations = conversation
        else:
            is_batched = False
            conversations = [conversation]

        # Users might still be passing processing kwargs in `**kwargs` so we need to filter
        # out additional kwargs that the template expects via Jinja2 template introspection
        # We strip unrelated kwargs to avoid passing unrecognized kwargs to `_merge_kwargs`.
        processor_kwargs = processor_kwargs or {}
        template_kwargs = _get_template_variables(chat_template)
        processor_kwargs_from_kwargs = {k: v for k, v in kwargs.items() if k not in template_kwargs}
        if processor_kwargs_from_kwargs:
            logger.warning(
                "Kwargs passed to `processor.__call__` have to be in `processor_kwargs` dict, not in `**kwargs`"
            )
            processor_kwargs = processor_kwargs_from_kwargs

        if return_tensors:
            processor_kwargs["return_tensors"] = return_tensors
        output_kwargs = self._merge_kwargs(
            VoxtralProcessorKwargs,
            **processor_kwargs,
        )
        text_kwargs = output_kwargs["text_kwargs"]
        audio_kwargs = output_kwargs["audio_kwargs"]
        return_tensors = text_kwargs.get("return_tensors", None)

        if return_tensors != "pt":
            raise ValueError(f"{self.__class__.__name__} only supports `return_tensors='pt'`.")

        tokenizer_kwargs = output_kwargs["text_kwargs"]
        tokenizer_kwargs["return_tensors"] = None  # let's not return tensors here
        encoded_instruct_inputs = self.tokenizer.apply_chat_template(conversations, **tokenizer_kwargs)

        if text_kwargs.get("tokenize", False):
            if text_kwargs.get("return_dict", False):
                audio = encoded_instruct_inputs.pop("audio", None)
                data = dict(encoded_instruct_inputs)
                if audio is not None:
                    max_source_positions = audio_kwargs.pop("max_source_positions")
                    data["input_features"] = self._retrieve_input_features(audio, max_source_positions, **audio_kwargs)

                return BatchFeature(data=data, tensor_type=return_tensors)

        if not is_batched:
            return encoded_instruct_inputs[0]

        return encoded_instruct_inputs