def get_video_replacement(item_idx: int):
            video, metadata = mm_items["video"][item_idx]
            patch_size = hf_processor.config.patch_size
            downsample_ratio = hf_processor.config.downsample_ratio
            target_patches = hf_processor.video_target_num_patches

            if target_patches is not None and video is not None and video.shape[0] > 0:
                orig_h, orig_w = video.shape[1], video.shape[2]
                _, _, feature_size = get_video_target_size_and_feature_size(
                    orig_w=orig_w,
                    orig_h=orig_h,
                    target_patches=target_patches,
                    maintain_aspect_ratio=hf_processor.video_maintain_aspect_ratio,
                    patch_size=patch_size,
                    downsample_ratio=downsample_ratio,
                )
            else:
                feature_size = hf_processor.num_image_token
            num_patches = video_num_patches[item_idx]
            if num_patches is not None:
                assert isinstance(num_patches, int)

            T = hf_processor.video_temporal_patch_size
            if T > 1 and num_patches is not None:
                num_tubelets = math.ceil(num_patches / T)
            else:
                num_tubelets = num_patches

            video_pruning_rate = self.info.ctx.get_mm_config().video_pruning_rate
            if video_pruning_rate is not None and video_pruning_rate > 0.0:
                # Start of EVS-specific code
                num_tokens = compute_retained_tokens_count(
                    tokens_per_frame=feature_size,
                    num_frames=num_tubelets,
                    q=video_pruning_rate,
                )
                # Here we just need placeholders that won't actually be replaced -
                # we just need to make sure the total number of tokens is correct
                # assign all tokens to the first frame
                tokens_per_frame = [num_tokens] + [0] * (num_tubelets - 1)

                # End of EVS-specific code
            else:
                tokens_per_frame = [feature_size] * num_tubelets

            frame_duration_ms = int(1000 / metadata["fps"])
            return hf_processor.get_video_repl(
                tokens_per_frame=tokens_per_frame,
                frames_indices=metadata["frames_indices"],
                frame_duration_ms=frame_duration_ms,
                tokenizer=hf_processor.tokenizer,
                img_start_token_ids=hf_processor._img_start_token_ids,
                img_end_token_ids=hf_processor._img_end_token_ids,
                img_context_token_ids=hf_processor._img_context_token_ids,
                video_temporal_patch_size=T,
            )