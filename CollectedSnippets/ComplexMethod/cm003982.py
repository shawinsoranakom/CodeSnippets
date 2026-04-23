def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        audio: AudioInput | None = None,
        videos: VideoInput | None = None,
        **kwargs: Unpack[Gemma4ProcessorKwargs],
    ) -> BatchFeature:
        if text is None and images is None and audio is None and videos is None:
            raise ValueError("Provide at least one of `text`, `images`, `audio`, or `videos`.")

        output_kwargs = self._merge_kwargs(
            Gemma4ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        image_inputs = {}
        if images is not None:
            images = self.image_processor.fetch_images(images)
            batched_images = make_nested_list_of_images(images)
            image_inputs = self.image_processor(images, **output_kwargs["images_kwargs"])

            num_soft_tokens = image_inputs.pop("num_soft_tokens_per_image")

            # Create empty text to be replaced with placeholders
            if not text:
                text = [" ".join([self.image_token] * len(images)) for images in batched_images]

            if len(batched_images) != len(text):
                raise ValueError(
                    f"Received inconsistently sized batches of images ({len(batched_images)}) and text ({len(text)})."
                )

            replacements = [f"{self.boi_token}{self.image_token * n}{self.eoi_token}" for n in num_soft_tokens]
            replacements_iter = iter(replacements)

            # Expand image_token placeholders to per-image soft token sequences.
            # re.sub never re-scans replaced text, so it is safe
            pattern = re.escape(self.image_token)
            text = [re.sub(pattern, lambda _: next(replacements_iter), prompt) for prompt in text]

        # Process video inputs in same way
        video_inputs = {}
        if videos is not None:
            video_inputs = self.video_processor(videos=videos, **output_kwargs["videos_kwargs"])
            num_video_tokens = video_inputs.pop("num_soft_tokens_per_video")

            # If user has not requested video metadata, pop it so it isn't returned
            if not kwargs.get("return_metadata"):
                video_metadata = video_inputs.pop("video_metadata")
            else:
                video_metadata = video_inputs["video_metadata"]

            video_replacements = []
            for metadata, n_tokens in zip(video_metadata, num_video_tokens):
                if metadata.fps is None:
                    logger.warning_once(
                        "Gemma 4 requires frame timestamps to construct prompts, but the `fps` of the input video "
                        "could not be inferred. Probably `video_metadata` was missing from inputs and you passed "
                        "pre-sampled frames. Defaulting to `fps=24`. Please provide `video_metadata` for more "
                        "accurate results."
                    )
                metadata.fps = 24 if metadata.fps is None else metadata.fps
                # mm:ss format for timestamps
                timestamp_str = [
                    f"{int(seconds // 60):02d}:{int(seconds % 60):02d}" for seconds in metadata.timestamps
                ]
                video_replacements.append(
                    " ".join(
                        [f"{t} {self.boi_token}{self.video_token * n_tokens}{self.eoi_token}" for t in timestamp_str]
                    )
                )

            video_replacements = iter(video_replacements)
            pattern = re.escape(self.video_token)
            text = [re.sub(pattern, lambda _: next(video_replacements), prompt) for prompt in text]

        # Process audio inputs
        audio_inputs = {}
        if audio is not None:
            if self.audio_token is None or self.boa_token is None or self.eoa_token is None:
                raise ValueError(
                    "Audio inputs were provided, but the tokenizer does not have an `audio_token` defined."
                )

            # Normalize audio input to list of waveforms
            if isinstance(audio, np.ndarray) and audio.ndim == 1:
                audio = [audio]

            # TODO: Add tests for audio-only processor inputs.
            if not text:
                text = [self.audio_token] * len(audio)

            # Dynamic audio token expansion wihtout padding:
            #   * Extract audio features with feature extractor;
            #   * Compute precise per-audio token counts from the waveform duration;
            #   * Generate full audio token sequence for each computed audio length;
            #   * Expand text prompts with full audio token sequences.
            audio_kwargs = output_kwargs.get("audio_kwargs", {})
            audio_inputs = self.feature_extractor(audio, **audio_kwargs)
            sampling_rate = self.feature_extractor.sampling_rate
            num_audio_tokens = [self._compute_audio_num_tokens(a, sampling_rate) for a in audio]
            replacements = [f"{self.boa_token}{self.audio_token * n}{self.eoa_token}" for n in num_audio_tokens]
            replacements_iter = iter(replacements)
            audio_pattern = re.escape(self.audio_token)
            text = [re.sub(audio_pattern, lambda _: next(replacements_iter), prompt) for prompt in text]

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        return_mm_token_type_ids = output_kwargs["text_kwargs"].pop("return_mm_token_type_ids", False)
        text_inputs = self.tokenizer(text=text, **output_kwargs["text_kwargs"])

        # Check special tokens for all active modalities
        active_modalities = []
        if images is not None:
            active_modalities.append("image")
        if videos is not None:
            active_modalities.append("video")
        if audio is not None:
            active_modalities.append("audio")
        if active_modalities:
            self._check_special_mm_tokens(text, text_inputs, modalities=active_modalities)

        if return_mm_token_type_ids:
            text_inputs["mm_token_type_ids"] = self.create_mm_token_type_ids(text_inputs["input_ids"])

        return BatchFeature(
            data={**text_inputs, **image_inputs, **audio_inputs, **video_inputs},
            tensor_type=return_tensors,
        )