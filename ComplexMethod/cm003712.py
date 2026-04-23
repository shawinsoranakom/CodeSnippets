def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        **kwargs: Unpack[InstructBlipProcessorKwargs],
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify at least images or text.")

        output_kwargs = self._merge_kwargs(
            InstructBlipProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        return_tensors = output_kwargs["text_kwargs"].pop("return_tensors", None)
        encoding = {}
        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not isinstance(text, list) and not isinstance(text[0], str):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")

            qformer_text_encoding = self.qformer_tokenizer(text, **output_kwargs["text_kwargs"])
            encoding["qformer_input_ids"] = qformer_text_encoding.pop("input_ids")
            encoding["qformer_attention_mask"] = qformer_text_encoding.pop("attention_mask")

            # We need this hacky manipulation because BLIP expects image tokens to be at the beginning even before BOS token
            if output_kwargs["text_kwargs"].get("max_length") is not None:
                output_kwargs["text_kwargs"]["max_length"] -= self.num_query_tokens
            text_encoding = self.tokenizer(text, **output_kwargs["text_kwargs"])

            if images is not None:
                # Image tokens should not be padded/truncated or prepended with special BOS token
                image_tokens = self.image_token.content * self.num_query_tokens
                output_kwargs["text_kwargs"]["add_special_tokens"] = False
                output_kwargs["text_kwargs"]["padding"] = False
                output_kwargs["text_kwargs"]["truncation"] = False
                image_text_encoding = self.tokenizer(image_tokens, **output_kwargs["text_kwargs"])
                for k in text_encoding:
                    text_encoding[k] = [image_text_encoding[k] + sample for sample in text_encoding[k]]
            encoding.update(text_encoding)

        if images is not None:
            image_encoding = self.image_processor(images, **output_kwargs["images_kwargs"])
            encoding.update(image_encoding)

        # Cast to desired return tensors type
        encoding = BatchFeature(encoding, tensor_type=return_tensors)
        return encoding