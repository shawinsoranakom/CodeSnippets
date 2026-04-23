def get_video_repl(
        cls,
        *,
        tokens_per_frame: list[int],
        frames_indices: list[int],
        frame_duration_ms: int,
        tokenizer: HfTokenizer,
        img_start_token_ids: list[int],
        img_end_token_ids: list[int],
        img_context_token_ids: list[int],
        video_temporal_patch_size: int = 1,
    ) -> PromptUpdateDetails[list[int]]:
        """
        Build prompt replacement for a video.
        The replacement returned is not actually used to replace the placeholder
        tokens - it's just used to make sure we allocate the correct number
        of tokens.
        Actual replacement is done in embed_multimodal of
        NemotronH_Nano_VL_V2
        (specifically in _process_video_input -> _create_final_video_embeddings).
        There, we create the final embeddings with text embeddings for indicator tokens
        and video embeddings for video tokens.
        This is a single function that handles all cases - non EVS, EVS dummy, EVS real.
        The differentiation is done via tokens_per_frame parameter.
        - non EVS case - constant value same value across all frames
        - EVS dummy - Doesn't matter how tokens are distributed between frames - just
                        make sure the total number of tokens is correct.
        - EVS real (called from get_real_video_repl_for_evs) - different value per frame
        Args:
            tokens_per_frame (list[int]): number of tokens per frame
                (one per tubelet when T > 1)
            frames_indices (list[int]): orig. frame indices
                (one per frame, before tubelet subsampling)
            frame_duration_ms (int): duration of each frame in milliseconds
            tokenizer (TokenizerLike): tokenizer to use for tokenizing frame separators
            img_start_token_ids (list[int]): pre-tokenized IMG_START tokens
            img_end_token_ids (list[int]): pre-tokenized IMG_END tokens
            img_context_token_ids (list[int]): pre-tokenized IMG_CONTEXT tokens
            video_temporal_patch_size (int): temporal patch size for videos
        """
        # TODO: Add support of frame_duration_ms to be None
        # At preprocessing step we should allow absent / metadata without
        # frames_indices field.
        timestamps_enabled = frame_duration_ms is not None
        T = video_temporal_patch_size
        num_frames = len(frames_indices)

        if T > 1 and timestamps_enabled:
            all_timestamps = calculate_timestamps(frames_indices, frame_duration_ms)

            frame_separators = []
            for group_idx, i in enumerate(range(0, num_frames, T)):
                group_frames = []
                for j in range(T):  # Every frame in the group
                    frame_idx = i + j
                    if frame_idx < num_frames:
                        # Valid idx (haven't padded to mult. of T yet)
                        ts = all_timestamps[frame_idx]
                        frame_str = "Frame" if j == 0 else "frame"
                        group_frames.append(
                            f"{frame_str} {frame_idx + 1} sampled at {ts:.2f} seconds"
                        )
                if group_frames:
                    # Join by `and` if there are >1 frame, otherwise no `and`
                    # Prepend \n to match training format (except first group)
                    sep = " and ".join(group_frames) + ": "
                    if group_idx > 0:
                        sep = "\n" + sep
                    frame_separators.append(sep)
        elif timestamps_enabled:
            timestamps = calculate_timestamps(frames_indices, frame_duration_ms)

            assert len(timestamps) == len(tokens_per_frame), (
                "timestamps and tokens_per_frame must have the same length"
            )
            frame_separators = [
                ("\n" if i > 0 else "")
                + f"Frame {i + 1} sampled at {timestamp:.2f} seconds: "
                for i, timestamp in enumerate(timestamps)
            ]
        else:
            frame_separators = [
                ("\n" if i > 0 else "") + f"Frame {i + 1}: "
                for i, _ in enumerate(tokens_per_frame)
            ]

        # Batch-tokenize all frame separators at once — the HuggingFace
        # tokenizers Rust backend parallelizes batch encoding across threads.
        batch_encoded = tokenizer(
            frame_separators,
            add_special_tokens=False,
            return_attention_mask=False,
        )
        frame_separators_tokenized: list[list[int]] = batch_encoded["input_ids"]

        # Tokenize each component independently to avoid tokenizer merging tokens
        # across boundaries. This ensures consistent tokenization regardless of
        # num_tokens_per_frame values.
        all_token_ids = []
        for i, num_tokens in enumerate(tokens_per_frame):
            all_token_ids.extend(frame_separators_tokenized[i])
            all_token_ids.extend(img_start_token_ids)
            all_token_ids.extend(img_context_token_ids * num_tokens)
            all_token_ids.extend(img_end_token_ids)

        return PromptUpdateDetails.from_seq(all_token_ids)