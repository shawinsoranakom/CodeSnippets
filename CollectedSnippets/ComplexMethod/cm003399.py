def __call__(
        self,
        images: ImageInput | None = None,
        text: str | list[str] | TextInput | PreTokenizedInput | None = None,
        **kwargs: Unpack[DonutProcessorKwargs],
    ):
        if images is None and text is None:
            raise ValueError("You need to specify either an `images` or `text` input to process.")

        output_kwargs = self._merge_kwargs(
            DonutProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if images is not None:
            inputs = self.image_processor(images, **output_kwargs["images_kwargs"])
        if text is not None:
            if images is not None:
                output_kwargs["text_kwargs"].setdefault("add_special_tokens", False)
            encodings = self.tokenizer(text, **output_kwargs["text_kwargs"])

        if text is None:
            return inputs
        elif images is None:
            return encodings
        else:
            inputs["labels"] = encodings["input_ids"]  # for BC
            inputs["input_ids"] = encodings["input_ids"]
            return inputs