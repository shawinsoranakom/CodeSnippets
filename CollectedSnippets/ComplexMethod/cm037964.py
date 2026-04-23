def iter_mm_grid_thw(
        self, mm_features: list[MultiModalFeatureSpec]
    ) -> Iterator[tuple[int, int, int, int]]:
        spatial_merge_size = self.config.vision_config.spatial_merge_size

        for mm_feature in sorted(mm_features, key=lambda f: f.mm_position.offset):
            if mm_feature.data is None:
                raise ValueError("M-RoPE calculation requires multimodal feature data")

            if mm_feature.modality == "image":
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
                    mm_feature.mm_position.offset,
                    t,
                    h // spatial_merge_size,
                    w // spatial_merge_size,
                )
            elif mm_feature.modality == "video":
                current_offset = mm_feature.mm_position.offset
                for t, h, w in self._split_video_grid_thw(
                    mm_feature.data["video_grid_thw"].data
                ):
                    llm_grid_h = h // spatial_merge_size
                    llm_grid_w = w // spatial_merge_size
                    yield (current_offset, t, llm_grid_h, llm_grid_w)
                    current_offset += t * llm_grid_h * llm_grid_w
            else:
                raise ValueError(f"Unsupported modality: {mm_feature.modality}")