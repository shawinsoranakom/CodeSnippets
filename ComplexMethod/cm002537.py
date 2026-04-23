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
        return_tensors: str | TensorType | None = None,
        return_dict: bool = False,
        load_audio_from_video: bool = False,
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
        processor_kwargs = processor_kwargs or {}

        if chat_template is None:
            if isinstance(self.chat_template, dict) and "default" in self.chat_template:
                chat_template = self.chat_template["default"]
            elif isinstance(self.chat_template, dict):
                raise ValueError(
                    'The processor has multiple chat templates but none of them are named "default". You need to specify'
                    " which one to use by passing the `chat_template` argument. Available templates are: "
                    f"{', '.join(self.chat_template.keys())}"
                )
            elif self.chat_template is not None:
                chat_template = self.chat_template
            else:
                raise ValueError(
                    "Cannot use apply_chat_template because this processor does not have a chat template."
                )
        else:
            if isinstance(self.chat_template, dict) and chat_template in self.chat_template:
                # It's the name of a template, not a full template string
                chat_template = self.chat_template[chat_template]
            else:
                # It's a template string, render it directly
                pass

        # Users might still be passing processing kwargs in `**kwargs` so we need to filter
        # out additional kwargs that the template expects via Jinja2 template introspection
        template_kwargs = _get_template_variables(chat_template)
        processor_kwargs_from_kwargs = {k: v for k, v in kwargs.items() if k not in template_kwargs}
        if processor_kwargs_from_kwargs:
            logger.warning(
                "Kwargs passed to `processor.__call__` have to be in `processor_kwargs` dict, not in `**kwargs`"
            )
            processor_kwargs = processor_kwargs_from_kwargs

        # Check if tokenizer is fast - use backend attribute if available, otherwise fall back to class name
        is_tokenizers_fast = False
        if hasattr(self, "tokenizer"):
            if hasattr(self.tokenizer, "backend"):
                is_tokenizers_fast = self.tokenizer.backend == "tokenizers"
            else:
                # Fallback to class name check
                is_tokenizers_fast = self.tokenizer.__class__.__name__.endswith("Fast")

        if continue_final_message:
            if add_generation_prompt:
                raise ValueError(
                    "continue_final_message and add_generation_prompt are not compatible. Use continue_final_message when you want the model to continue the final message, and add_generation_prompt when you want to add a header that will prompt it to start a new assistant message instead."
                )
            if return_assistant_tokens_mask:
                raise ValueError("continue_final_message is not compatible with return_assistant_tokens_mask.")

        if return_assistant_tokens_mask:
            if not is_tokenizers_fast:
                raise ValueError(
                    "`return_assistant_tokens_mask` is not possible with slow tokenizers. Make sure you have `tokenizers` installed. "
                    "If the error persists, open an issue to support a Fast tokenizer for your model."
                )
            else:
                processor_kwargs["return_offsets_mapping"] = (
                    True  # force offset mapping so we can infer token boundaries
                )

        # Set the sampling rate to load the audio files if user hasn't already passed with `kwargs`
        sampling_rate = kwargs.get("sampling_rate", processor_kwargs.get("sampling_rate"))
        if sampling_rate is None:
            if hasattr(self, "feature_extractor") and hasattr(self.feature_extractor, "sampling_rate"):
                sampling_rate = self.feature_extractor.sampling_rate
            else:
                sampling_rate = 16_000

        if isinstance(conversation, (list, tuple)) and (
            isinstance(conversation[0], (list, tuple)) or hasattr(conversation[0], "content")
        ):
            is_batched = True
            conversations = conversation
        else:
            is_batched = False
            conversations = [conversation]

        # Normalize OpenAI-style "image_url" content blocks to HuggingFace-style "image" blocks
        # OpenAI format: {"type": "image_url", "image_url": {"url": "..."}}
        # HuggingFace format: {"type": "image", "url": "..."}
        for conversation_idx, conversation in enumerate(conversations):
            for message in conversation:
                if not isinstance(message.get("content"), list):
                    continue
                new_content = []
                for content in message["content"]:
                    if isinstance(content, dict) and content.get("type") == "image_url" and "image_url" in content:
                        image_url_info = content["image_url"]
                        url = image_url_info.get("url", "") if isinstance(image_url_info, dict) else image_url_info
                        new_content.append({"type": "image", "url": url})
                    else:
                        new_content.append(content)
                message["content"] = new_content

        if tokenize:
            batch_images, batch_videos = [], []
            batch_audios = []
            for conversation in conversations:
                images, videos = [], []
                for message in conversation:
                    content = message.get("content") or []
                    visuals = [
                        content_block for content_block in content if content_block["type"] in ["image", "video"]
                    ]
                    audio_fnames = [
                        content_block[key]
                        for content_block in content
                        for key in ["audio", "url", "path"]
                        if key in content_block and content_block["type"] == "audio"
                    ]
                    image_fnames = [
                        vision_info[key]
                        for vision_info in visuals
                        for key in ["image", "url", "path", "base64"]
                        if key in vision_info and vision_info["type"] == "image"
                    ]
                    images.extend(image_fnames)
                    video_fnames = [
                        vision_info[key]
                        for vision_info in visuals
                        for key in ["video", "url", "path"]
                        if key in vision_info and vision_info["type"] == "video"
                    ]
                    videos.extend(video_fnames)

                    # Audio models do not accept nested list of audios (yet!) so we construct a flat input audio list
                    if not load_audio_from_video:
                        for fname in audio_fnames:
                            batch_audios.append(load_audio(fname, sampling_rate=sampling_rate))
                    else:
                        for fname in video_fnames:
                            # This updates the template in-place and adds audio entry
                            # to ensure `audio` token is added by jinja
                            message["content"].append({"type": "audio"})
                            batch_audios.append(load_audio(fname, sampling_rate=sampling_rate))

                # Currently all processors can accept nested list of batches, but not flat list of visuals
                # So we'll make a batched list of images and let the processor handle it
                batch_images.append(images)
                batch_videos.append(videos)

        # `kwargs` overwrite special tokens if both are present
        template_kwargs = {**self.tokenizer.special_tokens_map, **kwargs}
        prompt, generation_indices = render_jinja_template(
            conversations=conversations,
            tools=tools,
            documents=documents,
            chat_template=chat_template,
            return_assistant_tokens_mask=return_assistant_tokens_mask,
            continue_final_message=continue_final_message,
            add_generation_prompt=add_generation_prompt,
            **template_kwargs,
        )

        if not is_batched:
            prompt = prompt[0]

        if tokenize:
            # Tokenizer's `apply_chat_template` never adds special tokens when tokenizing
            # But processor's `apply_chat_template` didn't have an option to tokenize, so users had to format the prompt
            # and pass it to the processor. Users thus never worried about special tokens relying on processor handling
            # everything internally. The below line is to keep BC for that and be able to work with model that have
            # special tokens in the template (consistent with tokenizers). We dont want to raise warning, it will flood command line
            # without actionable solution for users
            single_prompt = prompt[0] if is_batched else prompt
            if self.tokenizer.bos_token is not None and single_prompt.startswith(self.tokenizer.bos_token):
                processor_kwargs["add_special_tokens"] = False

            # Always sample frames by default unless explicitly set to `False` by users. If users do not pass `num_frames`/`fps`
            # sampling should not done for BC.
            if "do_sample_frames" not in processor_kwargs and (
                processor_kwargs.get("fps") is not None or processor_kwargs.get("num_frames") is not None
            ):
                processor_kwargs["do_sample_frames"] = True

            # Set only is user passes a non-None value. Otherwise wa want to use each processor's own defaults
            if return_tensors:
                processor_kwargs["return_tensors"] = return_tensors

            images_exist = any((im is not None) for im_list in batch_images for im in im_list)
            videos_exist = any((vid is not None) for vid_list in batch_videos for vid in vid_list)
            out = self(
                text=prompt,
                images=batch_images if images_exist else None,
                videos=batch_videos if videos_exist else None,
                audio=batch_audios if batch_audios else None,
                **processor_kwargs,
            )

            if return_dict:
                if return_assistant_tokens_mask:
                    assistant_masks = []
                    offset_mapping = out.pop("offset_mapping")
                    input_ids = out["input_ids"]
                    for i in range(len(input_ids)):
                        current_mask = [0] * len(input_ids[i])
                        offsets = offset_mapping[i]
                        offset_starts = [start for start, end in offsets]
                        for assistant_start_char, assistant_end_char in generation_indices[i]:
                            start_pos = bisect.bisect_left(offset_starts, assistant_start_char)
                            end_pos = bisect.bisect_left(offset_starts, assistant_end_char)

                            if not (
                                start_pos >= 0
                                and start_pos < len(offsets)
                                and offsets[start_pos][0] <= assistant_start_char < offsets[start_pos][1]
                            ):
                                # start_token is out of bounds maybe due to truncation.
                                continue
                            # Ensure end_pos is also within bounds
                            if end_pos > len(input_ids[i]):
                                end_pos = len(input_ids[i])
                            for token_id in range(start_pos, end_pos if end_pos else len(input_ids[i])):
                                current_mask[token_id] = 1
                        assistant_masks.append(current_mask)
                    out["assistant_masks"] = assistant_masks
                    out.convert_to_tensors(tensor_type=return_tensors)
                return out
            else:
                return out["input_ids"]
        return prompt