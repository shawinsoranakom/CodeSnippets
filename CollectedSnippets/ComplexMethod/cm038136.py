def apply(
        self,
        inputs: ProcessorInputs,
        timing_ctx: TimingContext,
    ) -> MultiModalInput:
        mm_config = self.info.ctx.model_config.get_multimodal_config()
        merged_kwargs = mm_config.merge_mm_processor_kwargs(
            inputs.hf_processor_mm_kwargs
        )
        use_audio_in_video = bool(merged_kwargs.get("use_audio_in_video", False))

        inputs.hf_processor_mm_kwargs = {
            k: v
            for k, v in inputs.hf_processor_mm_kwargs.items()
            if k != "use_audio_in_video"
        }

        if not (use_audio_in_video and "video" in inputs.mm_data_items):
            return super().apply(inputs, timing_ctx)

        mm_items = inputs.mm_data_items
        if "audio" in mm_items:
            # Audio was pre-populated by upstream (e.g., OpenAI chat endpoint).
            # Reuse existing audio items; validate 1:1 correspondence.
            videos = mm_items.get_items("video", VideoProcessorItems)
            audios = mm_items.get_items("audio", AudioProcessorItems)
            if len(audios) != len(videos):
                raise ValueError(
                    "use_audio_in_video requires equal number of audio and "
                    f"video items, got num_audios={len(audios)}, "
                    f"num_videos={len(videos)}"
                )
            audio_items = audios.get_all()
            has_audio = [True] * len(videos)
            logger.info(
                "Using %d pre-populated audio item(s) from upstream.",
                len(audio_items),
            )
        else:
            # Extract audio from video bytes (library usage path).
            mm_items, audio_items, has_audio = self._extract_audio_from_videos(mm_items)
            inputs.mm_data_items = mm_items
            logger.info(
                "Extracted audio from video bytes: %d audio(s), has_audio=%s.",
                len(audio_items),
                has_audio,
            )

        if not audio_items:
            return super().apply(inputs, timing_ctx)

        prompt = inputs.prompt
        tokenizer = self.info.get_tokenizer()
        if not isinstance(prompt, str):
            prompt = tokenizer.decode(prompt, skip_special_tokens=False)

        # Inject AUDIO_CONTEXT only after <video> tokens whose video
        # actually contained an audio stream (preserving video-audio pairing).
        tag = "<video>"
        head, *rest = prompt.split(tag)
        rebuilt = [head]
        for append_audio, part in zip(has_audio, rest, strict=True):
            rebuilt.append(tag)
            if append_audio:
                rebuilt.append(AUDIO_CONTEXT)
            rebuilt.append(part)
        prompt = "".join(rebuilt)

        inputs.prompt = tokenizer.encode(prompt, add_special_tokens=False)

        if inputs.tokenization_kwargs is None:
            inputs.tokenization_kwargs = {}

        # Bypass the cached path: the HF processor must receive the
        # prompt (with injected <so_embedding>) and the audio data
        # together so it can perform audio-token replacement natively.
        (
            prompt_ids,
            mm_info,
            is_update_applied,
        ) = self._apply_hf_processor(inputs, timing_ctx)

        with timing_ctx.record("apply_prompt_updates"):
            prompt_ids, mm_placeholders = self._maybe_apply_prompt_updates(
                mm_items=mm_items,
                prompt_ids=prompt_ids,
                mm_kwargs=mm_info.kwargs,
                mm_prompt_updates=mm_info.prompt_updates,
                is_update_applied=is_update_applied,
            )

        mm_placeholder_ranges = {
            modality: [item.to_range() for item in placeholders]
            for modality, placeholders in mm_placeholders.items()
        }

        return MultiModalInput(
            type="multimodal",
            prompt_token_ids=prompt_ids,
            mm_kwargs=mm_info.kwargs,
            mm_hashes=mm_info.hashes,
            mm_placeholders=mm_placeholder_ranges,
        )