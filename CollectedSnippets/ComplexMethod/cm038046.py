def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        mm_data = dict(mm_data)
        processor = self.info.get_hf_processor(**mm_kwargs)

        # Separate video processing from image processing. Because the videos
        # are processed into several image patches
        if videos := mm_data.pop("videos", []):
            video_grid_thw_lst = []
            pixel_values_videos_lst = []
            timestamps_per_video = []

            for item in videos:
                video_array, metadata = item

                # NOTE: @JJJYmmm new attr metadata.frames_indices indicates
                # the sampled frames indices of pre-sampled videos, which is
                # used to calculate the timestamps. Make sure that
                # do_sample_frames in mm_kwargs is false for presampled videos.

                # NOTE: a copy of is created to update do_sample_frames,
                # otherwise mm_hash for the object will be incorrect.
                video_mm_kwargs = dict(**mm_kwargs)
                if "do_sample_frames" not in video_mm_kwargs:
                    # qwen_vl_utils already has "do_sample_frames" in
                    # mm_kwargs, don't overwrite it.
                    video_mm_kwargs["do_sample_frames"] = metadata.get(
                        "do_sample_frames", False
                    )

                metadata = VideoMetadata(
                    **{k: metadata[k] for k in metadata if k != "do_sample_frames"}
                )

                # Compute timestamps here where we have access to metadata
                timestamps = self.info._get_video_second_idx(
                    metadata=metadata,
                    do_sample_frames=video_mm_kwargs["do_sample_frames"],
                    sampled_fps=video_mm_kwargs.get("fps"),
                    sampled_num_frames=video_mm_kwargs.get("num_frames"),
                )
                timestamps_per_video.append(timestamps)

                video_mm_data = dict()
                video_mm_data["videos"] = [[video_array]]
                video_mm_data["video_metadata"] = [[metadata]]

                # When num_frames is specified, explicitly set fps=None
                # to prevent HF's BaseVideoProcessor.preprocess() from
                # filling in the class default (fps=2) via setdefault(),
                # which would conflict with num_frames (mutually exclusive).
                if "num_frames" in video_mm_kwargs and "fps" not in video_mm_kwargs:
                    video_mm_kwargs["fps"] = None

                video_outputs = super()._call_hf_processor(
                    prompt="<|vision_start|><|video_pad|><|vision_end|>",
                    mm_data=video_mm_data,
                    mm_kwargs=video_mm_kwargs,
                    tok_kwargs=tok_kwargs,
                )

                merge_size = processor.video_processor.merge_size
                # Get video grid info for EVS calculation.
                video_grid_thw = video_outputs["video_grid_thw"]
                num_frames = int(video_grid_thw[0, 0])
                tokens_per_frame_base = int(video_grid_thw[0, 1:].prod()) // (
                    merge_size**2
                )

                # Apply EVS if enabled.
                video_pruning_rate = self.info.ctx.get_mm_config().video_pruning_rate
                if video_pruning_rate is not None and video_pruning_rate > 0.0:
                    num_tokens = compute_retained_tokens_count(
                        tokens_per_frame=tokens_per_frame_base,
                        num_frames=num_frames,
                        q=video_pruning_rate,
                    )
                    # Here we just need placeholders that won't actually be replaced -
                    # we just need to make sure the total number of tokens is correct
                    # assign all tokens to the first frame.
                    tokens_per_frame = [num_tokens] + [0] * (num_frames - 1)
                    select_token_id = False
                else:
                    tokens_per_frame = [tokens_per_frame_base] * num_frames
                    select_token_id = True

                # Generate the video replacement with EVS-adjusted token counts
                tokenizer = self.info.get_tokenizer()
                hf_config = self.info.get_hf_config()
                video_repl = Qwen3VLMultiModalProcessor.get_video_repl(
                    tokens_per_frame=tokens_per_frame,
                    timestamps=timestamps,
                    tokenizer=tokenizer,
                    vision_start_token_id=hf_config.vision_start_token_id,
                    vision_end_token_id=hf_config.vision_end_token_id,
                    video_token_id=hf_config.video_token_id,
                    select_token_id=select_token_id,
                )

                # Convert token IDs to text for the HF processor flow
                video_placeholder = tokenizer.decode(
                    video_repl.full, skip_special_tokens=False
                )
                input_ids = video_outputs.pop("input_ids")
                video_placeholder = processor.tokenizer.batch_decode(input_ids)[0]
                prompt = prompt.replace(
                    "<|vision_start|><|video_pad|><|vision_end|>",
                    video_placeholder,
                    1,
                )

                video_grid_thw_lst.append(video_outputs["video_grid_thw"])
                pixel_values_videos_lst.append(video_outputs["pixel_values_videos"])
            video_outputs = dict(
                pixel_values_videos=torch.cat(pixel_values_videos_lst),
                video_grid_thw=torch.cat(video_grid_thw_lst),
                timestamps=timestamps_per_video,
            )
        else:
            video_outputs = dict()

        processed_outputs = super()._call_hf_processor(
            prompt=prompt,
            mm_data=mm_data,
            mm_kwargs=mm_kwargs,
            tok_kwargs=tok_kwargs,
        )
        combined_outputs = dict(
            processed_outputs,
            **video_outputs,
        )
        return BatchFeature(combined_outputs)