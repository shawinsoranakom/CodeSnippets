def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | list[TextInput] = None,
        **kwargs: Unpack[Kosmos2_5ProcessorKwargs],
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify either images or text.")

        if images is None:
            raise ValueError("Kosmos2_5Processor requires images to be passed.")

        output_kwargs = self._merge_kwargs(
            Kosmos2_5ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        encoding = BatchFeature()

        if images is not None:
            image_encoding = self.image_processor(images, **output_kwargs["images_kwargs"])
            image_encoding.pop("rows")
            image_encoding.pop("cols")
            encoding.update(image_encoding)

        prompt = f"{self.tokenizer.bos_token}{self.image_start_token}{self.image_token * self.num_image_tokens}{self.image_end_token}"

        if text is not None:
            if isinstance(text, str):
                text = [prompt + text]
            else:
                text = [prompt + t for t in text]
            input = self.tokenizer(text, **output_kwargs["text_kwargs"])

            batch_size, seq_len = input.input_ids.shape
            image_embeds_position_mask = [0, -1] + [1] * self.num_image_tokens + [-1]
            image_embeds_position_mask += [0] * (seq_len - len(image_embeds_position_mask))
            image_embeds_position_mask = (
                torch.LongTensor(image_embeds_position_mask).unsqueeze(0).repeat(batch_size, 1)
            )

            encoding.update(
                {
                    "input_ids": input.input_ids,
                    "attention_mask": input.attention_mask,
                    "image_embeds_position_mask": image_embeds_position_mask,
                }
            )

        return encoding