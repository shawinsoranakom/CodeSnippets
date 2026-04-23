def iter_mm_grid_thw(
        self, mm_features: list[MultiModalFeatureSpec]
    ) -> Iterator[tuple[int, int, int, int]]:
        spatial_merge_size = self.config.vision_config.spatial_merge_size

        for mm_feature in sorted(mm_features, key=lambda f: f.mm_position.offset):
            if mm_feature.data is None:
                raise ValueError("M-RoPE calculation requires multimodal feature data")

            embed_ranges = mm_feature.mm_position.extract_embeds_range()
            if mm_feature.modality == "image":
                assert len(embed_ranges) == 1
                grid_thw = mm_feature.data["image_grid_thw"].data
                if isinstance(grid_thw, torch.Tensor):
                    if grid_thw.ndim == 2:
                        assert grid_thw.shape[0] == 1
                        t, h, w = grid_thw[0].tolist()
                    else:
                        t, h, w = grid_thw.tolist()
                else:
                    if isinstance(grid_thw[0], list):
                        assert len(grid_thw) == 1
                        t, h, w = grid_thw[0]
                    else:
                        t, h, w = grid_thw

                yield (
                    embed_ranges[0][0],
                    t,
                    h // spatial_merge_size,
                    w // spatial_merge_size,
                )
            elif mm_feature.modality == "video":
                split_video_grids = split_thw(mm_feature.data["video_grid_thw"].data)
                assert len(embed_ranges) == split_video_grids.shape[0]
                for (start_idx, end_idx), (t, h, w) in zip(
                    embed_ranges, split_video_grids.tolist()
                ):
                    llm_grid_h = h // spatial_merge_size
                    llm_grid_w = w // spatial_merge_size
                    num_mm_tokens = t * llm_grid_h * llm_grid_w
                    assert end_idx - start_idx + 1 == num_mm_tokens
                    yield (start_idx, t, llm_grid_h, llm_grid_w)
            else:
                raise ValueError(f"Unsupported modality: {mm_feature.modality}")