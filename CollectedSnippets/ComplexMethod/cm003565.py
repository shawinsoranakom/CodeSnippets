def __call__(
        self,
        images: ImageInput | None = None,
        text: TextInput | list[TextInput] = None,
        **kwargs: Unpack[Kosmos2ProcessorKwargs],
    ) -> BatchFeature:
        if images is None and text is None:
            raise ValueError("You have to specify either images or text.")

        output_kwargs = self._merge_kwargs(
            Kosmos2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )

        bboxes = output_kwargs["images_kwargs"].pop("bboxes", None)
        num_image_tokens = output_kwargs["images_kwargs"].pop("num_image_tokens", 64)
        first_image_token_id = output_kwargs["images_kwargs"].pop("first_image_token_id", None)
        add_eos_token = output_kwargs["text_kwargs"].pop("add_eos_token", False)

        add_special_tokens = output_kwargs["text_kwargs"]["add_special_tokens"]
        padding = output_kwargs["text_kwargs"]["padding"]
        return_tensors = output_kwargs["text_kwargs"].setdefault("return_tensors", None)

        encoding = BatchFeature()

        if images is not None:
            image_encoding = self.image_processor(images, **output_kwargs["images_kwargs"])
            encoding.update(image_encoding)

        if text is not None:
            text = self.preprocess_examples(text, images, bboxes, num_image_tokens=num_image_tokens)

            if add_special_tokens and not add_eos_token:
                if isinstance(text, str):
                    text = f"{self.tokenizer.bos_token}{text}"
                elif isinstance(text, list):
                    text = [f"{self.tokenizer.bos_token}{s}" for s in text]
            output_kwargs["text_kwargs"]["add_special_tokens"] = (
                output_kwargs["text_kwargs"]["add_special_tokens"] and add_eos_token
            )
            output_kwargs["text_kwargs"]["padding"] = padding if images is None else False
            output_kwargs["text_kwargs"]["return_tensors"] = return_tensors if images is None else None
            text_encoding = self.tokenizer(text=text, **output_kwargs["text_kwargs"])
            encoding.update(text_encoding)

        output_kwargs["text_kwargs"]["add_special_tokens"] = add_special_tokens
        output_kwargs["text_kwargs"]["padding"] = padding
        output_kwargs["text_kwargs"]["return_tensors"] = return_tensors

        if text is not None and images is not None:
            # Use the id of the first token after <unk>
            if first_image_token_id is None:
                first_image_token_id = self.tokenizer.unk_token_id + 1

            # To see if we need one more `0` (for `<s>`) at the beginning of `image_embeds_position_mask`.
            with_bos = add_special_tokens

            # The first (actual) `<image>` token is always at the 1st or 2nd place (after `<s>` if any). Here we look
            # for the second `<image>` token (which indicate the first image token).
            start_index = int(with_bos) + 1

            # Add `image_embeds_position_mask`: the leading and trailing `0` are for `boi` and `eoi` tokens. The `1` indicates
            # the places of image tokens.
            image_token_ids = list(range(first_image_token_id, first_image_token_id + num_image_tokens))
            base_image_embeds_position_mask = [0] + [1] * num_image_tokens + [0]

            # loop over `encoding["input_ids"]`
            input_ids = []
            image_embeds_position_mask = []
            all_input_ids = encoding["input_ids"]
            # not batched -> (changed to) batch of size 1
            if isinstance(text, str):
                all_input_ids = [all_input_ids]
                encoding["attention_mask"] = [encoding["attention_mask"]]
            for text_ids in all_input_ids:
                # change the ids for the fake `<image>` tokens in `input_ids`
                text_ids = text_ids[:start_index] + image_token_ids + text_ids[start_index + num_image_tokens :]
                input_ids.append(text_ids)

                mask = copy.copy(base_image_embeds_position_mask)
                if with_bos:
                    # for `<s>`
                    mask = [0] + mask
                # trailing part (which are not related to the image)
                mask += [0] * (len(text_ids) - len(mask))
                image_embeds_position_mask.append(mask)

            if isinstance(text, list):
                sorted_length = sorted(
                    [(idx, len(x)) for idx, x in enumerate(text_encoding.input_ids)], key=lambda x: x[-1]
                )
                _, min_len_not_padded = sorted_length[0]
                idx, _ = sorted_length[-1]
                output_kwargs["text_kwargs"]["add_special_tokens"] = (
                    output_kwargs["text_kwargs"]["add_special_tokens"] and add_eos_token
                )
                output_kwargs["text_kwargs"]["return_tensors"] = None

                text_encoding = self.tokenizer(text=[text[idx]], **output_kwargs["text_kwargs"])
                max_len_padded = len(text_encoding.input_ids[0])

                if min_len_not_padded != max_len_padded:
                    if self.tokenizer.padding_side == "right":
                        input_ids = [x + [self.tokenizer.pad_token_id] * (max_len_padded - len(x)) for x in input_ids]
                        image_embeds_position_mask = [
                            x + [0] * (max_len_padded - len(x)) for x in image_embeds_position_mask
                        ]
                        encoding["attention_mask"] = [
                            x + [0] * (max_len_padded - len(x)) for x in encoding["attention_mask"]
                        ]
                    elif self.tokenizer.padding_side == "left":
                        input_ids = [[self.tokenizer.pad_token_id] * (max_len_padded - len(x)) + x for x in input_ids]
                        image_embeds_position_mask = [
                            [0] * (max_len_padded - len(x)) + x for x in image_embeds_position_mask
                        ]
                        encoding["attention_mask"] = [
                            [0] * (max_len_padded - len(x)) + x for x in encoding["attention_mask"]
                        ]

            # un-batch if necessary
            if isinstance(text, str) and return_tensors is None:
                input_ids = input_ids[0]
                encoding["attention_mask"] = encoding["attention_mask"][0]
                image_embeds_position_mask = image_embeds_position_mask[0]

            # update (with the target tensor type if specified)
            encoding.update(
                BatchEncoding(
                    data={
                        "input_ids": input_ids,
                        "attention_mask": encoding["attention_mask"],
                        "image_embeds_position_mask": image_embeds_position_mask,
                    },
                    tensor_type=return_tensors,
                )
            )

        return encoding