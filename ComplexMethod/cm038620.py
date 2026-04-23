async def _preprocess_speech_to_text(
        self,
        request: SpeechToTextRequest,
        audio_data: bytes,
        request_id: str,
    ) -> tuple[list[EngineInput], float]:
        # Validate request
        request.language = self.model_cls.validate_language(request.language)
        request.to_language = (
            self.model_cls.validate_language(request.to_language)
            if request.to_language
            else None
        )

        if len(audio_data) / 1024**2 > self.max_audio_filesize_mb:
            raise VLLMValidationError(
                "Maximum file size exceeded",
                parameter="audio_filesize_mb",
                value=len(audio_data) / 1024**2,
            )

        # Decode audio bytes.  For container formats (MP4, M4A, WebM) that
        # soundfile cannot detect from a BytesIO stream, _load_audio_bytes
        # transparently falls back to ffmpeg via an in-memory fd.
        # NOTE resample to model SR here for efficiency. This is also a
        # pre-requisite for chunking, as it assumes Whisper SR.
        try:
            with io.BytesIO(audio_data) as buf:
                y, sr = load_audio(buf, sr=self.asr_config.sample_rate)
        except Exception as exc:
            raise ValueError("Invalid or unsupported audio file.") from exc

        duration = get_audio_duration(y=y, sr=sr)
        do_split_audio = self.asr_config.allow_audio_chunking and (
            self.asr_config.max_audio_clip_s is not None
            and duration > self.asr_config.max_audio_clip_s
        )

        if not do_split_audio:
            chunks = [y]
        else:
            assert self.asr_config.max_audio_clip_s is not None
            assert self.asr_config.min_energy_split_window_size is not None
            chunks = split_audio(
                audio_data=y,
                sample_rate=int(sr),
                max_clip_duration_s=self.asr_config.max_audio_clip_s,
                overlap_duration_s=self.asr_config.overlap_chunk_second,
                min_energy_window_size=self.asr_config.min_energy_split_window_size,
            )

        if request.language is None and getattr(
            self.model_cls, "supports_explicit_language_detection", False
        ):
            # Auto-detect language from the first chunk.
            request.language = await self._detect_language(
                chunks[0], f"{request_id}-lang_detect"
            )

        parsed_prompts: list[DictPrompt] = []
        for chunk in chunks:
            stt_params = request.build_stt_params(
                audio=chunk,
                stt_config=self.asr_config,
                model_config=self.model_config,
                task_type=self.task_type,
            )
            prompt = self.model_cls.get_generation_prompt(stt_params)

            parsed_prompt: DictPrompt
            if request.response_format == "verbose_json":
                parsed_prompt = parse_enc_dec_prompt(prompt)
                parsed_prompt = self._preprocess_verbose_prompt(parsed_prompt)
            else:
                parsed_prompt = parse_model_prompt(self.model_config, prompt)

            parsed_prompts.append(parsed_prompt)

        engine_inputs = await self.renderer.render_cmpl_async(parsed_prompts)

        return engine_inputs, duration