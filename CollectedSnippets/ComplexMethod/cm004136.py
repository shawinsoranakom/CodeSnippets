def get_rope_index(
        self,
        input_ids: torch.LongTensor | None = None,
        image_grid_thw: torch.LongTensor | None = None,
        images_per_sample: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Calculate the 3D rope index for image generation task with full batch support.

        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens in the vocabulary.
            image_grid_thw (`torch.LongTensor` of shape `(total_images_in_batch, 3)`, *optional*):
                The temporal, height and width of feature shape of each image.
                Images are packed across all samples in the batch.
            images_per_sample (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
                Number of images (including target grids) for each sample in the batch.
                Used to split image_grid_thw by sample.
            attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on padding token indices.

        Returns:
            position_ids (`torch.LongTensor` of shape `(3, batch_size, sequence_length)`):
                Position IDs for temporal, height, and width dimensions.
            mrope_position_deltas (`torch.Tensor` of shape `(batch_size, 1)`):
                Position deltas for multi-modal rotary position embedding.
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device
        dtype = input_ids.dtype

        image_start_token_id = self.config.image_start_token_id
        image_end_token_id = self.config.image_end_token_id

        position_ids = torch.ones(3, batch_size, seq_len, dtype=dtype, device=device)
        text_positions = torch.arange(seq_len, device=device)[None, :].repeat(3, 1)

        # Split image_grid_thw by sample if images_per_sample is provided
        if image_grid_thw is not None and images_per_sample is not None:
            grids_per_sample = torch.split(image_grid_thw, images_per_sample.tolist())
        elif image_grid_thw is not None:
            # Fallback: assume all grids belong to first sample (batch_size=1)
            grids_per_sample = [image_grid_thw] * batch_size
        else:
            grids_per_sample = [None] * batch_size

        # Per-sample caches for decode stage
        all_decode_position_ids = []

        for batch_idx in range(batch_size):
            curr_input_ids = input_ids[batch_idx]
            curr_grids = grids_per_sample[batch_idx]

            if attention_mask is not None and attention_mask.shape[1] == seq_len:
                valid_mask = attention_mask[batch_idx] == 1
                curr_input_ids_valid = curr_input_ids[valid_mask]
            else:
                # attention_mask may have different length during assisted decoding
                curr_input_ids_valid = curr_input_ids
                valid_mask = None

            # Find image boundaries in this sample
            image_end_positions = torch.where(curr_input_ids_valid == image_end_token_id)[0]
            image_start_positions = torch.where(curr_input_ids_valid == image_start_token_id)[0] + 1
            num_complete_images = len(image_end_positions)

            current_pos = 0
            prev_image_end = 0
            curr_position_ids = []

            # Process complete images (source images in image-to-image task)
            for img_idx, (start, end) in enumerate(zip(image_start_positions, image_end_positions)):
                if curr_grids is None or img_idx >= len(curr_grids):
                    break

                # Text tokens before this image
                llm_pos_length = start - prev_image_end
                llm_position_ids = text_positions[:, current_pos : current_pos + llm_pos_length].to(device=device)
                current_pos += llm_position_ids.shape[-1]

                # Image tokens with 2D spatial encoding
                # For an image with height H and width W:
                # - position_width cycles [0, 1, ..., W-1] for each row, repeated H times
                # - position_height stays constant per row, [0]*W, [1]*W, ..., [H-1]*W
                vision_position_ids = self.get_vision_position_ids(
                    start_position=current_pos, grid_thw=curr_grids[img_idx], device=device
                )
                current_pos += max(curr_grids[img_idx][1], curr_grids[img_idx][2])

                prev_image_end = end
                curr_position_ids.append(torch.cat([llm_position_ids, vision_position_ids], dim=-1))

            # Remaining text tokens (including the final image_start token for generation)
            end_position = len(curr_input_ids_valid) - prev_image_end
            llm_position_ids = text_positions[:, current_pos : current_pos + end_position].to(device=device)
            current_pos += llm_position_ids.shape[-1]
            curr_position_ids.append(llm_position_ids)

            # Concatenate all position ids for this sample
            curr_position_ids = torch.cat(curr_position_ids, dim=-1)

            # Store in the main position_ids tensor
            if valid_mask is not None:
                position_ids[:, batch_idx, valid_mask] = curr_position_ids
            else:
                position_ids[:, batch_idx, :] = curr_position_ids

            # Build decode position ids for this sample
            if curr_grids is not None and len(curr_grids) > 0:
                num_decode_grids = len(curr_grids) - num_complete_images
                num_decode_grids = max(num_decode_grids, 0)
                decode_pos = current_pos

                decode_temporal_list = []
                decode_height_list = []
                decode_width_list = []

                curr_grids_list = curr_grids.tolist()
                for i in range(1, num_decode_grids + 1):
                    grid_idx = -i
                    h = curr_grids_list[grid_idx][1]
                    w = curr_grids_list[grid_idx][2]
                    total_tokens = h * w

                    h_indices = torch.arange(h, device=device).unsqueeze(1).expand(h, w).flatten()
                    w_indices = torch.arange(w, device=device).unsqueeze(0).expand(h, w).flatten()

                    decode_temporal_list.append(
                        torch.full((total_tokens,), decode_pos, device=device, dtype=torch.long)
                    )
                    decode_height_list.append(decode_pos + h_indices)
                    decode_width_list.append(decode_pos + w_indices)
                    decode_pos = decode_pos + max(h, w)

                # End marker
                decode_temporal_list.append(torch.tensor([decode_pos], device=device, dtype=torch.long))
                decode_height_list.append(torch.tensor([decode_pos], device=device, dtype=torch.long))
                decode_width_list.append(torch.tensor([decode_pos], device=device, dtype=torch.long))

                sample_decode_pos_ids = torch.stack(
                    [
                        torch.cat(decode_temporal_list, dim=0),
                        torch.cat(decode_height_list, dim=0),
                        torch.cat(decode_width_list, dim=0),
                    ],
                    dim=0,
                )
                all_decode_position_ids.append(sample_decode_pos_ids)

        # Store prefill length (same for all samples since input_ids is padded to same length)
        self._prefill_len = seq_len

        # Pad decode position ids to same length and stack
        if all_decode_position_ids:
            max_decode_len = max(x.shape[1] for x in all_decode_position_ids)
            padded_decode_pos_ids = [
                F.pad(pos_ids, (0, max_decode_len - pos_ids.shape[1]), mode="replicate")
                for pos_ids in all_decode_position_ids
            ]
            self._cached_decode_position_ids = torch.stack(padded_decode_pos_ids, dim=0)  # [batch, 3, max_decode_len]
        else:
            self._cached_decode_position_ids = None

        mrope_position_deltas = torch.zeros([batch_size, 1], dtype=dtype, device=device)

        return position_ids, mrope_position_deltas