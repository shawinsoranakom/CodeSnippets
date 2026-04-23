def _call_hf_processor(
        self,
        prompt: str,
        mm_data: Mapping[str, object],
        mm_kwargs: Mapping[str, object],
        tok_kwargs: Mapping[str, object],
    ) -> BatchFeature:
        # Validate max_soft_tokens early and exit cleanly on bad values.
        _SUPPORTED_SOFT_TOKENS = (70, 140, 280, 560, 1120)

        merged_kwargs = self.info.ctx.get_merged_mm_kwargs(mm_kwargs)
        val = merged_kwargs.get("max_soft_tokens")
        if val is None:
            val = merged_kwargs.get("images_kwargs", {}).get("max_soft_tokens")

        if val is not None and val not in _SUPPORTED_SOFT_TOKENS:
            raise ValueError(
                f"Unsupported max_soft_tokens value: {val}. "
                f"Valid values are {_SUPPORTED_SOFT_TOKENS}."
            )

        mm_data = dict(mm_data)

        # ---- VIDEO HANDLING ----
        # Gemma4 decomposes video into timestamped image frames.
        # Each frame is processed with max_soft_tokens=70 through the
        # same vision tower, matching transformers processing_gemma4.py.
        video_outputs: dict[str, Any] = {}
        if videos := mm_data.pop("videos", []):
            processor = self.info.get_hf_processor()

            all_video_pixel_values: list[torch.Tensor] = []
            all_video_position_ids: list[torch.Tensor] = []
            video_num_soft_tokens_per_video: list[list[int]] = []
            video_timestamps_per_video: list[list[float]] = []
            video_frame_counts: list[int] = []

            video_replacements: list[str] = []

            for item in videos:
                video_array, metadata = item

                # Convert frames to PIL images
                if isinstance(video_array, np.ndarray):
                    frames = [
                        PILImage.fromarray(video_array[i])
                        for i in range(video_array.shape[0])
                    ]
                else:
                    frames = list(video_array)

                # Compute timestamps from metadata (same as transformers)
                fps = metadata.get("fps") or 24
                frame_indices = metadata.get("frames_indices", list(range(len(frames))))
                timestamps = [idx / fps for idx in frame_indices]

                # Process frames as images with max_soft_tokens=70
                video_mm_kwargs = dict(mm_kwargs)
                video_mm_kwargs["max_soft_tokens"] = _VIDEO_MAX_SOFT_TOKENS

                dummy_prompt = ("\t" + processor.image_token) * len(frames)

                frame_outputs = super()._call_hf_processor(
                    prompt=dummy_prompt,
                    mm_data={"images": frames},
                    mm_kwargs=video_mm_kwargs,
                    tok_kwargs=tok_kwargs,
                )

                # Remap HF key name
                if "image_position_ids" in frame_outputs:
                    frame_outputs["pixel_position_ids"] = frame_outputs.pop(
                        "image_position_ids"
                    )

                all_video_pixel_values.append(frame_outputs["pixel_values"])
                all_video_position_ids.append(frame_outputs["pixel_position_ids"])

                # Compute soft tokens per frame
                num_soft_per_frame = []
                for img in frames:
                    w, h = img.size
                    n = self.info._compute_num_soft_tokens(
                        w, h, max_soft_tokens=_VIDEO_MAX_SOFT_TOKENS
                    )
                    num_soft_per_frame.append(n)

                video_num_soft_tokens_per_video.append(num_soft_per_frame)
                video_timestamps_per_video.append(timestamps)
                video_frame_counts.append(len(frames))

                # Build expanded replacement text for this video.
                ts_strs = [f"{int(s // 60):02d}:{int(s % 60):02d}" for s in timestamps]
                replacement = " ".join(
                    f"{t} {processor.boi_token}"
                    f"{processor.video_token * n}"
                    f"{processor.eoi_token}"
                    for t, n in zip(ts_strs, num_soft_per_frame)
                )
                video_replacements.append(replacement)

            # Replace all <|video|> placeholders at once. We split on
            # video_token to get N+1 parts, then interleave with the
            # N replacement strings. This avoids the iterative
            # split-replace bug where replacement text (which itself
            # contains <|video|> tokens) collides with later splits.
            vt = processor.video_token
            parts = prompt.split(vt, len(video_replacements))

            # NOTE: len(parts) <= len(video_replacements) + 1
            parts_with_repl: list[str] = []
            for part, repl in zip(parts, video_replacements):
                parts_with_repl.extend([part, repl])
            parts_with_repl.extend(parts[len(video_replacements) :])

            prompt = "".join(parts_with_repl)

            video_outputs = {
                "pixel_values_videos": torch.cat(all_video_pixel_values, dim=0),
                "pixel_position_ids_videos": torch.cat(all_video_position_ids, dim=0),
                "video_frame_counts": torch.tensor(video_frame_counts),
                "video_num_soft_tokens": video_num_soft_tokens_per_video,
                "video_timestamps": video_timestamps_per_video,
            }

        # The processor accepts 'audio' not 'audios'.
        if "audios" in mm_data:
            mm_data["audio"] = mm_data.pop("audios")

        # Warn if any audio waveform exceeds the model's max duration.
        if "audio" in mm_data:
            processor = self.info.get_hf_processor()
            sr = processor.feature_extractor.sampling_rate
            max_tokens = processor.audio_seq_length
            ms_per_tok = processor.audio_ms_per_token
            max_duration_s = max_tokens * ms_per_tok / 1000.0
            audios = mm_data["audio"]
            if not isinstance(audios, (list, tuple)):
                audios = [audios]
            for i, waveform in enumerate(audios):
                duration_s = len(waveform) / sr
                if duration_s > max_duration_s:
                    logger.warning(
                        "Audio duration exceeds max: %f > %f seconds",
                        duration_s,
                        max_duration_s,
                    )
        # vLLM's call_hf_processor (context.py) re-merges
        # mm_processor_kwargs from the model config on every call via:
        #   config_kwargs | incoming_kwargs  (right side wins)
        #
        # If we strip max_soft_tokens from incoming, the re-merge puts
        # back the config's global default (e.g. 280), ignoring any
        # per-prompt override.  Instead, we keep it in the kwargs with
        # the validated per-prompt value so it wins during the merge.
        #
        # NOTE: This requires a corresponding type annotation on the
        # HF side (Gemma4ProcessorKwargs.images_kwargs) so that
        # _merge_kwargs routes max_soft_tokens into images_kwargs.
        patched_mm_kwargs = dict(mm_kwargs)
        if val is not None:
            patched_mm_kwargs["max_soft_tokens"] = val

        processed_outputs = super()._call_hf_processor(
            prompt,
            mm_data,
            patched_mm_kwargs,
            tok_kwargs,
        )

        # HF uses 'image_position_ids'; vLLM uses 'pixel_position_ids'.
        # Remap here to keep a single translation point.
        if "image_position_ids" in processed_outputs:
            processed_outputs["pixel_position_ids"] = processed_outputs.pop(
                "image_position_ids"
            )

        if "input_features" in processed_outputs:
            # Unpad per-item so each item's cache entry is
            # self-contained. The batched() field config in
            # _get_mm_fields_config will re-pad all fields to the
            # batch's max length at batch time, ensuring consistent
            # padding regardless of cache history.
            masks = processed_outputs["input_features_mask"]
            unpadded_features = [
                f[mask]
                for f, mask in zip(
                    processed_outputs["input_features"],
                    masks,
                )
            ]
            unpadded_masks = [mask[mask] for mask in masks]
            processed_outputs["input_features"] = unpadded_features
            processed_outputs["input_features_padded"] = unpadded_features
            processed_outputs["input_features_mask"] = unpadded_masks

        # Merge video outputs into the final result
        combined_outputs = dict(processed_outputs, **video_outputs)
        return BatchFeature(combined_outputs)