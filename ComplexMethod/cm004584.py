def _get_image_nums_and_video_nums(
        self,
        input_ids: torch.LongTensor | None,
        inputs_embeds: torch.Tensor | None = None,
        image_grid_thw: torch.LongTensor | None = None,
        image_merge_sizes: torch.LongTensor | None = None,
        video_grid_thw: torch.LongTensor | None = None,
        video_merge_sizes: torch.LongTensor | None = None,
        video_compression_mask: torch.BoolTensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Get the number of images and videos for each sample to calculate the separation length of the sample tensor.
        These parameters are not passed through the processor to avoid unpredictable impacts from interface modifications.

        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary.

        Returns:
            image_nums (`torch.LongTensor` of shape `(batch_size, num_images_sample)`)
            video_nums (`torch.LongTensor` of shape `(batch_size, num_videos_sample)`)
        """
        image_token_id = self.config.image_token_id
        video_token_id = self.config.video_token_id

        if inputs_embeds is not None:
            image_mask = (
                inputs_embeds
                == self.get_input_embeddings()(
                    torch.tensor(image_token_id, dtype=torch.long, device=inputs_embeds.device)
                )
            )[..., 0]
            video_mask = (
                inputs_embeds
                == self.get_input_embeddings()(
                    torch.tensor(video_token_id, dtype=torch.long, device=inputs_embeds.device)
                )
            )[..., 0]
        else:
            image_mask = input_ids == image_token_id
            video_mask = input_ids == video_token_id

        if image_grid_thw is not None:
            num_image_features = image_grid_thw.prod(dim=1) // (image_merge_sizes**2)
        else:
            num_image_features = []

        if video_grid_thw is not None:
            num_video_features = video_grid_thw.prod(dim=1) // (video_merge_sizes**2)
            if video_compression_mask is not None:
                num_video_features = video_compression_mask.split(num_video_features.tolist())
                num_video_features = [mask.sum() for mask in num_video_features]
        else:
            num_video_features = []

        image_nums, video_nums = [], []
        start_image_idx, start_video_idx = 0, 0

        for num_image_tokens, num_video_tokens in zip(image_mask.sum(dim=1), video_mask.sum(dim=1)):
            cu_num_features = 0
            image_idx = start_image_idx
            while image_idx < len(num_image_features) and cu_num_features < num_image_tokens:
                cu_num_features += num_image_features[image_idx]
                image_idx += 1
            assert cu_num_features == num_image_tokens, (
                "The number of image tokens does not match the number of image features."
            )
            image_nums.append(image_idx - start_image_idx)
            start_image_idx = image_idx

            cu_num_features = 0
            video_idx = start_video_idx
            while video_idx < len(num_video_features) and cu_num_features < num_video_tokens:
                cu_num_features += num_video_features[video_idx]
                video_idx += 1
            assert cu_num_features == num_video_tokens, (
                "The number of video tokens does not match the number of video features."
            )
            video_nums.append(video_idx - start_video_idx)
            start_video_idx = video_idx

        return image_nums, video_nums