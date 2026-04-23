def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        audio: np.ndarray | list[float] | list[np.ndarray] | list[list[float]] | None = None,
        **kwargs: Unpack[Gemma3nProcessorKwargs],
    ) -> BatchFeature:
        if text is None and images is None and audio is None:
            raise ValueError("Provide at least one of `text`, `images`, or `audio`.")

        output_kwargs = self._merge_kwargs(
            Gemma3nProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if isinstance(text, str):
            text = [text]
        elif not isinstance(text, list) and not isinstance(text[0], str):
            raise TypeError("Invalid input text. Please provide a string, or a list of strings")

        if audio is not None:
            audio_inputs = self.feature_extractor(audio, **output_kwargs["audio_kwargs"])

            if not text:
                text = [self.audio_token for _ in audio]

            # Expand placeholder audio tokens to the full audio token sequence
            text = [prompt.replace(self.audio_token, self.full_audio_sequence) for prompt in text]
        else:
            audio_inputs = {}

        if images is not None:
            images = self.image_processor.fetch_images(images)
            batched_images = make_nested_list_of_images(images)
            image_inputs = self.image_processor(batched_images, **output_kwargs["images_kwargs"])

            # Create empty text to be replaced with placeholders
            if not text:
                text = [" ".join([self.image_token] * len(images)) for images in batched_images]

            if len(batched_images) != len(text):
                raise ValueError(
                    f"Received inconsistently sized batches of images ({len(batched_images)}) and text ({len(text)})."
                )

            # Expand placeholder image tokens to the full image token sequence
            text = [prompt.replace(self.image_token, self.full_image_sequence) for prompt in text]
        else:
            image_inputs = {}

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        text_inputs = self.tokenizer(text=text, **output_kwargs["text_kwargs"], return_tensors="np")
        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        # Add token type ids manually, as tokenizer can't do arbitrary position token types
        array_ids = text_inputs["input_ids"]
        token_type_ids = np.zeros_like(array_ids)
        token_type_ids[array_ids == self.image_token_id] = 1
        token_type_ids[array_ids == self.audio_token_id] = 3
        text_inputs = {k: v.tolist() for k, v in text_inputs.items()}  # in case user requested list inputs
        text_inputs["token_type_ids"] = token_type_ids.tolist()
        return BatchFeature(data={**text_inputs, **image_inputs, **audio_inputs}, tensor_type=return_tensors)