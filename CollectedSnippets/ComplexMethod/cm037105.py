def _preprocess_video(
        self,
        text: list[str],
        videos: list[tuple[npt.NDArray, dict[str, Any]]],
    ) -> tuple[list[str], dict[str, Any]]:
        if len(videos) == 0 or not self.supports_video:
            return text, {}

        videos_lst = [v[0] for v in videos]
        video_metadata_lst = [v[1] for v in videos]

        pixel_values_lst_video = self._videos_to_pixel_values_lst(
            videos_lst,
            dtype=self.dtype,
        )

        # We use frame duration in milliseconds (as integer) to ensure
        # we have consistent timestamps calculation. At preprocessing
        # fps parameter is given in fp32, while at inference it is bf16
        # which leads to inaccurate timestamp calculation and causes
        # timestamp values to differ.In rare cases this causes
        # mismatching number of output tokens for tokenized  frame prefixes
        frame_duration_ms_lst = [
            int(1000.0 / metadata["fps"]) for metadata in video_metadata_lst
        ]
        frames_indices_lst = [
            metadata["frames_indices"] for metadata in video_metadata_lst
        ]
        video_num_patches = torch.tensor([len(item) for item in pixel_values_lst_video])

        # Normalization already fused into resize above.
        # Skip the torch.cat copy when there is exactly one video
        if len(pixel_values_lst_video) == 1:
            pixel_values_flat = pixel_values_lst_video[0]
        else:
            pixel_values_flat = torch.cat(pixel_values_lst_video)
        video_inputs = {
            "pixel_values_flat_video": pixel_values_flat,
            "video_num_patches": video_num_patches,
            "frames_indices": frames_indices_lst,
            "frame_duration_ms": torch.tensor(frame_duration_ms_lst),
        }

        patch_size: int = self.config.patch_size
        downsample_ratio = self.config.downsample_ratio

        T = self.video_temporal_patch_size

        for pixel_values, video_metadata, frames_indices, frame_duration_ms in zip(
            pixel_values_lst_video,
            video_metadata_lst,
            frames_indices_lst,
            frame_duration_ms_lst,
        ):
            num_frames = pixel_values.shape[0]
            frame_h, frame_w = pixel_values.shape[-2], pixel_values.shape[-1]
            tokens_in_single_frame = int(
                (frame_h * frame_w // patch_size**2) * (downsample_ratio**2)
            )
            num_tubelets = math.ceil(num_frames / T) if T > 1 else num_frames

            if self.video_pruning_rate is not None and self.video_pruning_rate > 0.0:
                # Start of EVS-specific code
                num_tokens = compute_retained_tokens_count(
                    tokens_per_frame=tokens_in_single_frame,
                    num_frames=num_tubelets,
                    q=self.video_pruning_rate,
                )

                # Here we just need placeholders that won't actually be replaced -
                # we just need to make sure the total number of tokens is correct
                # assign all tokens to the first frame
                tokens_per_frame = [num_tokens] + [0] * (num_tubelets - 1)

                # End of EVS-specific code
            else:
                tokens_per_frame = [tokens_in_single_frame] * num_tubelets

            video_repl = self.get_video_repl(
                tokens_per_frame=tokens_per_frame,
                frames_indices=frames_indices,
                frame_duration_ms=frame_duration_ms,
                tokenizer=self.tokenizer,
                img_start_token_ids=self._img_start_token_ids,
                img_end_token_ids=self._img_end_token_ids,
                img_context_token_ids=self._img_context_token_ids,
                video_temporal_patch_size=T,
            )

            # video_repl.full is a list of token IDs
            # Convert token IDs back to text for the HF processor flow
            video_repl_text = self.tokenizer.decode(
                video_repl.full, skip_special_tokens=False
            )
            text = [t.replace("<video>", video_repl_text, 1) for t in text]

        return text, video_inputs