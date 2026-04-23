def __call__(
        self,
        images: ImageInput = None,
        text: TextInput
        | PreTokenizedInput
        | list[TextInput]
        | list[PreTokenizedInput] = None,
        videos: VideoInput = None,
        **kwargs,
    ) -> BatchFeature:
        image_inputs = {}
        if images is not None:
            image_inputs = self.image_processor(images=images)
            image_grid_thw = image_inputs["image_grid_thw"]

        if not isinstance(text, list):
            text = [text]

        text = text.copy()  # below lines change text in-place

        image_tokens_cumsum = [0]
        if images is not None:
            index = 0
            for i in range(len(text)):
                while self.image_token in text[i]:
                    grid_h, grid_w = image_grid_thw[index][-2:]
                    patch_h = grid_h // self.image_processor.merge_size
                    patch_w = grid_w // self.image_processor.merge_size
                    num_image_tokens = patch_h * (patch_w + 1) + 2
                    image_tokens_cumsum.append(
                        image_tokens_cumsum[-1] + num_image_tokens
                    )
                    # text[i] = text[i].replace(self.image_token, self.im_start_token + self.placeholder_token * num_image_tokens + self.im_end_token, 1) # noqa: E501
                    text[i] = text[i].replace(
                        self.image_token, self.placeholder_token * num_image_tokens, 1
                    )
                    index += 1
                text[i] = text[i].replace(self.placeholder_token, self.image_token)
                # text[i] = self.tokenizer.bos_token + text[i]

        text_inputs = self.tokenizer(text, add_special_tokens=False, **kwargs)
        self._check_special_mm_tokens(text, text_inputs, modalities=["image"])

        input_ids = text_inputs["input_ids"]
        position_ids = torch.arange(len(input_ids[0]))
        position_ids_w = torch.arange(len(input_ids[0]))
        position_ids_h = torch.arange(len(input_ids[0]))
        position_ids_t = torch.arange(len(input_ids[0]))

        if images is not None:
            image_token_pos_indices = torch.where(input_ids[0] == self.image_token_id)[
                0
            ]
            for i in range(len(image_grid_thw)):
                grid_h, grid_w = image_grid_thw[i][-2:]
                patch_h = grid_h // self.image_processor.merge_size
                patch_w = grid_w // self.image_processor.merge_size
                start_pos = image_token_pos_indices[image_tokens_cumsum[i]].item() + 1
                replace_num = (patch_w + 1) * patch_h
                position_ids_w[start_pos : start_pos + replace_num] = torch.tensor(
                    list(range(patch_w + 1)) * patch_h, dtype=torch.int64
                )
                patch_h_list = []
                for h in range(patch_h):
                    patch_h_list += [h] * (patch_w + 1)
                position_ids_h[start_pos : start_pos + replace_num] = torch.tensor(
                    patch_h_list, dtype=torch.int64
                )
                position_ids_t[start_pos : start_pos + replace_num] = 0

        position_ids = torch.stack(
            [position_ids, position_ids_w, position_ids_h, position_ids_t]
        ).unsqueeze(0)
        text_inputs["position_ids"] = position_ids

        attention_mask = input_ids.ne(self.pad_id)
        text_inputs["attention_mask"] = attention_mask
        text_inputs["imgs_pos"] = [self.get_imgs_pos(e) for e in input_ids]
        # image_inputs["imgs"] = [[image_inputs["pixel_values"]]]

        return_tensors = kwargs.pop("return_tensors", None)
        return BatchFeature(
            data={**text_inputs, **image_inputs},
            tensor_type=return_tensors,
        )