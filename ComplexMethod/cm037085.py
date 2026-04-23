def process_one(
        self,
        prompt: str,
        images: list[Image.Image],
        inference_mode: bool = True,
        **kwargs: Any,
    ):
        """

        Args:
            prompt (str): the formatted prompt;
            images (list[ImageType]): the list of images;
            inference_mode (bool): if True, then remove the last eos token;
            **kwargs: Additional keyword arguments.

        Returns:
            outputs (BaseProcessorOutput): the output of the processor,
                - input_ids (torch.LongTensor): [N + image tokens]
                - target_ids (torch.LongTensor): [N + image tokens]
                - pixel_values (torch.FloatTensor): [n_patches, 3, H, W]
                - image_id (int): the id of the image token
                - num_image_tokens (list[int]): the number of image tokens
        """

        assert prompt is not None and images is not None, (
            "prompt and images must be used at the same time."
        )

        sft_format = prompt
        (
            tokenized_str,
            images_list,
            images_seq_mask,
            images_spatial_crop,
            num_image_tokens,
        ) = self.tokenize_with_images(
            sft_format, images, bos=True, eos=True, cropping=len(images) <= 2
        )
        masked_tokenized_str = []
        for token_index in tokenized_str:
            if token_index != self.image_token_id:
                masked_tokenized_str.append(token_index)
            else:
                masked_tokenized_str.append(self.ignore_id)

        assert (
            len(tokenized_str) == len(images_seq_mask) == len(masked_tokenized_str)
        ), (
            f"tokenized_str's length {len(tokenized_str)}, input_ids' length {len(masked_tokenized_str)}, "
            f"imags_seq_mask's length {len(images_seq_mask)}, are not equal"
        )

        input_ids = torch.LongTensor(tokenized_str)
        target_ids = torch.LongTensor(masked_tokenized_str)
        images_seq_mask = torch.tensor(images_seq_mask, dtype=torch.bool)

        # set input_ids < 0 | input_ids == self.image_token_id as ignore_id
        target_ids[(input_ids < 0) | (input_ids == self.image_token_id)] = (
            self.ignore_id
        )
        input_ids[input_ids < 0] = self.pad_id

        if inference_mode:
            # Remove the ending eos token
            assert input_ids[-1] == self.eos_id
            input_ids = input_ids[:-1]
            target_ids = target_ids[:-1]
            images_seq_mask = images_seq_mask[:-1]

        if len(images_list) == 0:
            pixel_values = torch.zeros((1, 3, self.image_size, self.image_size))
            images_spatial_crop = torch.zeros((1, 2), dtype=torch.long)
        else:
            pixel_values = torch.stack(images_list, dim=0)
            images_spatial_crop = torch.tensor(images_spatial_crop, dtype=torch.long)

        input_ids = input_ids.unsqueeze(0)

        prepare = BatchFeature(
            data=dict(
                input_ids=input_ids,
                pixel_values=pixel_values,
                images_seq_mask=images_seq_mask,
                images_spatial_crop=images_spatial_crop,
                num_image_tokens=num_image_tokens,
            ),
            tensor_type="pt",
        )
        return prepare