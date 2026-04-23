async def _generate(
        self,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
        tools: Optional[str] = None,
        images: Optional[list["ImageInput"]] = None,
        videos: Optional[list["VideoInput"]] = None,
        audios: Optional[list["AudioInput"]] = None,
        **input_kwargs,
    ) -> AsyncIterator["RequestOutput"]:
        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        if images is not None and not any(IMAGE_PLACEHOLDER in message["content"] for message in messages):
            messages[0]["content"] = IMAGE_PLACEHOLDER * len(images) + messages[0]["content"]

        if videos is not None and not any(VIDEO_PLACEHOLDER in message["content"] for message in messages):
            messages[0]["content"] = VIDEO_PLACEHOLDER * len(videos) + messages[0]["content"]

        if audios is not None and not any(AUDIO_PLACEHOLDER in message["content"] for message in messages):
            messages[0]["content"] = AUDIO_PLACEHOLDER * len(audios) + messages[0]["content"]

        messages = self.template.mm_plugin.process_messages(
            messages, images or [], videos or [], audios or [], self.processor
        )
        paired_messages = messages + [{"role": "assistant", "content": ""}]
        prompt_ids, _ = self.template.encode_oneturn(self.tokenizer, paired_messages, system, tools)
        prompt_length = len(prompt_ids)

        temperature: Optional[float] = input_kwargs.pop("temperature", None)
        top_p: Optional[float] = input_kwargs.pop("top_p", None)
        top_k: Optional[float] = input_kwargs.pop("top_k", None)
        num_return_sequences: int = input_kwargs.pop("num_return_sequences", 1)
        repetition_penalty: Optional[float] = input_kwargs.pop("repetition_penalty", None)
        length_penalty: Optional[float] = input_kwargs.pop("length_penalty", None)
        skip_special_tokens: Optional[bool] = input_kwargs.pop("skip_special_tokens", None)
        max_length: Optional[int] = input_kwargs.pop("max_length", None)
        max_new_tokens: Optional[int] = input_kwargs.pop("max_new_tokens", None)
        stop: Optional[Union[str, list[str]]] = input_kwargs.pop("stop", None)

        if length_penalty is not None:
            logger.warning_rank0("Length penalty is not supported by the vllm engine yet.")

        if "max_new_tokens" in self.generating_args:
            max_tokens = self.generating_args["max_new_tokens"]
        elif "max_length" in self.generating_args:
            if self.generating_args["max_length"] > prompt_length:
                max_tokens = self.generating_args["max_length"] - prompt_length
            else:
                max_tokens = 1

        if max_length:
            max_tokens = max_length - prompt_length if max_length > prompt_length else 1

        if max_new_tokens:
            max_tokens = max_new_tokens

        sampling_params = SamplingParams(
            n=num_return_sequences,
            repetition_penalty=(
                repetition_penalty if repetition_penalty is not None else self.generating_args["repetition_penalty"]
            )
            or 1.0,  # repetition_penalty must > 0
            temperature=temperature if temperature is not None else self.generating_args["temperature"],
            top_p=(top_p if top_p is not None else self.generating_args["top_p"]) or 1.0,  # top_p must > 0
            top_k=(top_k if top_k is not None else self.generating_args["top_k"]) or -1,  # top_k must > 0
            stop=stop,
            stop_token_ids=self.template.get_stop_token_ids(self.tokenizer),
            max_tokens=max_tokens,
            skip_special_tokens=skip_special_tokens
            if skip_special_tokens is not None
            else self.generating_args["skip_special_tokens"],
        )

        multi_modal_data = {}
        if images is not None:  # add image features
            multi_modal_data["image"] = self.template.mm_plugin._regularize_images(
                images,
                image_max_pixels=self.model_args.image_max_pixels,
                image_min_pixels=self.model_args.image_min_pixels,
            )["images"]

        if videos is not None:
            multi_modal_data["video"] = self.template.mm_plugin._regularize_videos(
                videos,
                image_max_pixels=self.model_args.video_max_pixels,
                image_min_pixels=self.model_args.video_min_pixels,
                video_fps=self.model_args.video_fps,
                video_maxlen=self.model_args.video_maxlen,
            )["videos"]

        if audios is not None:
            audio_data = self.template.mm_plugin._regularize_audios(
                audios,
                sampling_rate=self.model_args.audio_sampling_rate,
            )
            multi_modal_data["audio"] = zip(audio_data["audios"], audio_data["sampling_rates"])

        result_generator = self.model.generate(
            {"prompt_token_ids": prompt_ids, "multi_modal_data": multi_modal_data or None},
            sampling_params=sampling_params,
            request_id=request_id,
            lora_request=self.lora_request,
        )
        return result_generator