def __call__(
        self,
        images: ImageInput | None = None,
        text: list[str] | list[list[str]] | None = None,
        **kwargs: Unpack[OmDetTurboProcessorKwargs],
    ) -> BatchFeature:
        if images is None or text is None:
            raise ValueError("You have to specify both `images` and `text`")

        output_kwargs = self._merge_kwargs(
            OmDetTurboProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        if isinstance(text, str):
            text = text.strip(" ").split(",")

        if not (len(text) and isinstance(text[0], (list, tuple))):
            text = [text]

        task = output_kwargs["text_kwargs"].pop("task", None)
        if task is None:
            task = [f"Detect {', '.join(text_single)}." for text_single in text]
        elif not isinstance(task, (list, tuple)):
            task = [task]

        encoding_image_processor = self.image_processor(images, **output_kwargs["images_kwargs"])
        tasks_encoding = self.tokenizer(text=task, **output_kwargs["text_kwargs"])

        classes = text

        classes_structure = torch.tensor([len(class_single) for class_single in classes], dtype=torch.long)
        classes_flattened = [class_single for class_batch in classes for class_single in class_batch]
        classes_encoding = self.tokenizer(text=classes_flattened, **output_kwargs["text_kwargs"])

        encoding = BatchFeature()
        encoding.update({f"tasks_{key}": value for key, value in tasks_encoding.items()})
        encoding.update({f"classes_{key}": value for key, value in classes_encoding.items()})
        encoding.update({"classes_structure": classes_structure})
        encoding.update(encoding_image_processor)

        return encoding