def __call__(
        self,
        images=None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[Pix2StructProcessorKwargs],
    ) -> BatchEncoding | BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify either images or text.")

        output_kwargs = self._merge_kwargs(
            Pix2StructProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        add_special_tokens = output_kwargs["text_kwargs"].pop("add_special_tokens", None)
        # Get only text
        if images is None and not self.image_processor.is_vqa:
            output_kwargs["text_kwargs"]["add_special_tokens"] = (
                add_special_tokens if add_special_tokens is not None else True
            )
            text_encoding = self.tokenizer(text=text, **output_kwargs["text_kwargs"])
            return text_encoding

        if not self.image_processor.is_vqa:
            # add pixel_values
            encoding_image_processor = self.image_processor(images, **output_kwargs["images_kwargs"])
        else:
            # add pixel_values and bbox
            output_kwargs["images_kwargs"].setdefault("header_text", text)
            encoding_image_processor = self.image_processor(images, **output_kwargs["images_kwargs"])

        if text is not None and not self.image_processor.is_vqa:
            output_kwargs["text_kwargs"]["add_special_tokens"] = (
                add_special_tokens if add_special_tokens is not None else False
            )
            text_encoding = self.tokenizer(text=text, **output_kwargs["text_kwargs"])

            if "attention_mask" in text_encoding:
                text_encoding["decoder_attention_mask"] = text_encoding.pop("attention_mask")
            if "input_ids" in text_encoding:
                text_encoding["decoder_input_ids"] = text_encoding.pop("input_ids")
        else:
            text_encoding = None

        if text_encoding is not None:
            encoding_image_processor.update(text_encoding)

        return encoding_image_processor