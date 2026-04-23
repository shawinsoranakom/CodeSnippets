def _get_prompt_updates(
        self,
        mm_items: MultiModalDataItems,
        hf_processor_mm_kwargs: Mapping[str, Any],
        out_mm_kwargs: MultiModalKwargsItems,
    ) -> Sequence[PromptUpdate]:
        hf_processor = self.info.get_hf_processor(**hf_processor_mm_kwargs)
        image_processor = self.info.get_image_processor(**hf_processor_mm_kwargs)
        tokenizer = self.info.get_tokenizer()
        vocab = tokenizer.get_vocab()
        image_token_id = vocab[hf_processor.image_token]
        video_token_id = vocab[hf_processor.video_token]
        placeholder = {"image": image_token_id, "video": video_token_id}
        merge_length = image_processor.merge_size**2

        out_mm_kwargs_data = out_mm_kwargs.get_data()
        frame_types: list[torch.Tensor] = hf_processor_mm_kwargs.get(
            "frame_types", None
        )
        timestamps: list[torch.Tensor] = hf_processor_mm_kwargs.get("timestamps", None)
        num_videos = mm_items.get_count("video", strict=False)

        if frame_types is None:
            frame_types = [None] * num_videos
        assert len(frame_types) == num_videos, (
            f"Number of frame_types={len(frame_types)} "
            f"doesn't equal to number of videos={num_videos}"
        )
        if timestamps is None:
            timestamps = [None] * num_videos
        assert len(timestamps) == num_videos, (
            f"Number of timestamps={len(timestamps)} "
            f"doesn't equal to number of videos={num_videos}"
        )

        video_grid_thw = out_mm_kwargs_data.get(
            "video_grid_thw", torch.empty((0, 3), dtype=torch.int64)
        )
        num_frames = out_mm_kwargs_data.get(
            "num_frames", torch.tensor([], dtype=torch.int64)
        )

        assert len(num_frames) == num_videos, (
            f"Size of num_frames={len(num_frames)} "
            f"doesn't equal to number of videos={num_videos}"
        )

        video_grid_hws = split_thw(video_grid_thw)
        assert int(num_frames.sum().tolist()) == video_grid_hws.shape[0], (
            f"The first dimension of `video_grid_hws`={video_grid_hws.shape[0]}"
            f"doesn't equal to num of frames."
        )

        cu_seqlens = torch.cumsum(torch.tensor([0] + num_frames.tolist()), dim=-1)

        def get_replacement_keye(item_idx: int, modality: str):
            """
            Args:
                item_idx(int): The item index of modality to replace
                modality(str): The modality
            """
            if modality == "image":
                out_item = out_mm_kwargs[modality][item_idx]
                grid_thw = out_item[f"{modality}_grid_thw"].data
                assert isinstance(grid_thw, torch.Tensor)

                num_tokens = int(grid_thw.prod()) // merge_length
                return [image_token_id] * num_tokens
            elif modality == "video":
                placeholders = []
                video_timestamps = timestamps[item_idx]
                video_frame_types = frame_types[item_idx]
                grid_thw = video_grid_hws[
                    cu_seqlens[item_idx] : cu_seqlens[item_idx + 1]
                ]

                nframes = grid_thw.shape[0]

                if video_timestamps is None:
                    video_timestamps = [""] * nframes
                else:
                    video_timestamps = [format(ts, ".1f") for ts in video_timestamps]

                if video_frame_types is None:
                    video_frame_types = [0] * nframes
                for i, sub_thw in enumerate(grid_thw):
                    s = f"{hf_processor.frame_token}{video_timestamps[i]}"
                    if video_frame_types[i] == 1:
                        s += hf_processor.fast_start
                    placeholders.extend(tokenizer.encode(s))
                    num_frame_tokens = int(sub_thw.prod()) // merge_length
                    placeholders.extend([video_token_id] * num_frame_tokens)
                    if video_frame_types[i] == 1:
                        placeholders.append(vocab[hf_processor.fast_end])

                return PromptUpdateDetails.select_token_id(
                    placeholders, embed_token_id=video_token_id
                )
            else:
                raise ValueError(f"Unsupported modality {modality}")

        return [
            PromptReplacement(
                modality=modality,
                target=[placeholder[modality]],
                replacement=partial(get_replacement_keye, modality=modality),
            )
            for modality in ("image", "video")
        ]