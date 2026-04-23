def _get_mrope_input_positions(
        input_tokens: list[int],
        mm_features: list[MultiModalFeatureSpec],
        config: Qwen3VLConfig,
    ):
        llm_pos_ids_list = []
        st = 0
        for (
            offset,
            llm_grid_h,
            llm_grid_w,
            actual_num_tokens,
        ) in Qwen3VLForConditionalGeneration._iter_mm_grid_hw(
            input_tokens,
            mm_features,
            video_token_id=config.video_token_id,
            vision_start_token_id=config.vision_start_token_id,
            vision_end_token_id=config.vision_end_token_id,
            spatial_merge_size=config.vision_config.spatial_merge_size,
        ):
            # Skip frames with 0 tokens (EVS placeholder with tokens lumped elsewhere)
            if actual_num_tokens == 0:
                continue

            text_len = offset - st
            st_idx = llm_pos_ids_list[-1].max() + 1 if len(llm_pos_ids_list) > 0 else 0
            llm_pos_ids_list.append(
                np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
            )

            # Check if this is a "lumped placeholder" (all tokens from multiple frames
            # assigned to the 0-th frame - see
            # `Qwen3VLMultiModalProcessor.get_video_repl`.
            expected_tokens_per_frame = llm_grid_h * llm_grid_w
            if actual_num_tokens > expected_tokens_per_frame:
                # Lumped placeholder: create grid positions for all "logical" frames
                # represented.
                num_logical_frames = actual_num_tokens // expected_tokens_per_frame
                remainder = actual_num_tokens % expected_tokens_per_frame

                # Create positions for complete frames.
                for _ in range(num_logical_frames):
                    grid_indices = np.indices((1, llm_grid_h, llm_grid_w)).reshape(
                        3, -1
                    )
                    llm_pos_ids_list.append(grid_indices + text_len + st_idx)
                    st_idx = llm_pos_ids_list[-1].max() + 1
                    text_len = 0  # No text between frames within the lump

                # Handle remainder tokens if any (partial frame).
                # NOTE: this should never be the case. Should we have an assert?
                if remainder > 0:
                    # Create a partial grid - take first 'remainder' positions
                    full_grid = np.indices((1, llm_grid_h, llm_grid_w)).reshape(3, -1)
                    grid_indices = full_grid[:, :remainder]
                    llm_pos_ids_list.append(grid_indices + text_len + st_idx)
            else:
                # Normal case: frame has exactly the expected tokens (after actual EVS
                # pruning).
                grid_indices = np.indices((1, llm_grid_h, llm_grid_w)).reshape(3, -1)
                llm_pos_ids_list.append(grid_indices + text_len + st_idx)

            st = offset + actual_num_tokens

        if st < len(input_tokens):
            st_idx = llm_pos_ids_list[-1].max() + 1 if len(llm_pos_ids_list) > 0 else 0
            text_len = len(input_tokens) - st
            llm_pos_ids_list.append(
                np.broadcast_to(np.arange(text_len), (3, text_len)) + st_idx
            )

        llm_positions = np.concatenate(llm_pos_ids_list, axis=1).reshape(3, -1)
        mrope_position_delta = (llm_positions.max() + 1 - len(input_tokens)).item()
        return torch.from_numpy(llm_positions), mrope_position_delta