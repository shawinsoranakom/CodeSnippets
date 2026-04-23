def __call__(
        self,
        images: VideoInput | None = None,
        text: TextInput | PreTokenizedInput | list[TextInput] | list[PreTokenizedInput] = None,
        add_special_tokens: bool = True,
        padding: bool | str | PaddingStrategy = False,
        truncation: bool | str | TruncationStrategy = None,
        max_length: int | None = None,
        stride: int = 0,
        pad_to_multiple_of: int | None = None,
        return_attention_mask: bool | None = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_token_type_ids: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        return_tensors: str | TensorType | None = None,
        **kwargs,
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify at least one of images or text.")

        encoding = {}
        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif not isinstance(text, list) and not isinstance(text[0], str):
                raise ValueError("Invalid input text. Please provide a string, or a list of strings")

            qformer_text_encoding = self.qformer_tokenizer(
                text=text,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                stride=stride,
                pad_to_multiple_of=pad_to_multiple_of,
                return_attention_mask=return_attention_mask,
                return_overflowing_tokens=return_overflowing_tokens,
                return_special_tokens_mask=return_special_tokens_mask,
                return_offsets_mapping=return_offsets_mapping,
                return_token_type_ids=return_token_type_ids,
                return_length=return_length,
                verbose=verbose,
                return_tensors=return_tensors,
                **kwargs,
            )
            encoding["qformer_input_ids"] = qformer_text_encoding.pop("input_ids")
            encoding["qformer_attention_mask"] = qformer_text_encoding.pop("attention_mask")

            # We need this hacky manipulation because BLIP expects image tokens to be at the beginning even before BOS token
            # InstrucBLIP works with 4 frames only
            if max_length is not None:
                max_length -= self.num_query_tokens
            text_encoding = self.tokenizer(
                text=text,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                stride=stride,
                pad_to_multiple_of=pad_to_multiple_of,
                return_attention_mask=return_attention_mask,
                return_overflowing_tokens=return_overflowing_tokens,
                return_special_tokens_mask=return_special_tokens_mask,
                return_offsets_mapping=return_offsets_mapping,
                return_token_type_ids=return_token_type_ids,
                return_length=return_length,
                verbose=verbose,
                return_tensors=None,  # required to concatenate below
                **kwargs,
            )

            if images is not None:
                video_tokens = self.video_token.content * self.num_query_tokens * 4
                video_text_encoding = self.tokenizer(
                    video_tokens,
                    add_special_tokens=False,  # required to concatenate below
                    return_attention_mask=return_attention_mask,
                    return_overflowing_tokens=return_overflowing_tokens,
                    return_special_tokens_mask=return_special_tokens_mask,
                    return_offsets_mapping=return_offsets_mapping,
                    return_token_type_ids=return_token_type_ids,
                    return_length=return_length,
                    return_tensors=None,
                )
                for k in text_encoding:
                    text_encoding[k] = [video_text_encoding[k] + sample for sample in text_encoding[k]]
            encoding.update(text_encoding)

        if images is not None:
            image_encoding = self.video_processor(images, return_tensors=return_tensors)
            encoding.update(image_encoding)

        encoding = BatchFeature(encoding, tensor_type=return_tensors)
        return encoding