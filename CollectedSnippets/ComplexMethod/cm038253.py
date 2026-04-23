def forward_videos(
        self,
        pixel_values_videos: list[list[torch.Tensor]],
    ) -> tuple[torch.Tensor, ...]:
        pixel_values_videos_flat = flatten_bn(
            [frame for frames in pixel_values_videos for frame in frames],
            concat=True,
        )

        visual_token_idx = 0 if "siglip" in self.vision_config.model_type else 1
        video_forward_outs = self.vision_model(pixel_values_videos_flat)[
            :, visual_token_idx:
        ]

        video_forward_outs = video_forward_outs.to(dtype=self.mm_projector.dtype)

        # Run MM-Projector
        # len(num_grids) == len(num_queries_vis_abstractors) + 1
        grid_idx = 0
        # e.g. [0, 9, 18, 19, 27, 28, 36, 37, 45, 46, 54, 55, 56]
        num_grids = [grid_idx]
        # e.g. [81, 81, 81, 9, 81, 9, 81, 9, 81, 9, 81, 9]
        num_queries_vis_abstractors = []
        len_total_frames = video_forward_outs.shape[0]

        if self.config.first_last_frames_slow:
            # slowfast (first_last_frames_slow)
            assert len_total_frames != 0
            if len_total_frames <= 2:
                num_queries_vis_abstractors.append(
                    self.config.num_queries_vis_abstractor_video_slow
                )
                grid_idx += len_total_frames
                num_grids.append(grid_idx)
            else:
                num_queries_vis_abstractors.append(
                    self.config.num_queries_vis_abstractor_video_slow
                )
                grid_idx += 1
                num_grids.append(grid_idx)

                num_queries_vis_abstractors.append(
                    self.config.num_queries_vis_abstractor_video_fast
                )
                grid_idx += len_total_frames - 2
                num_grids.append(grid_idx)

                num_queries_vis_abstractors.append(
                    self.config.num_queries_vis_abstractor_video_slow
                )
                grid_idx += 1
                num_grids.append(grid_idx)
        else:
            # slowfast
            for pixel_values_frames in pixel_values_videos:
                for pixel_values_frame in pixel_values_frames:
                    if len(pixel_values_frame) > 0:
                        num_queries_vis_abstractors.append(
                            self.config.num_queries_vis_abstractor_video_slow
                        )
                        grid_idx += 1
                        num_grids.append(grid_idx)
                        num_queries_vis_abstractors.append(
                            self.config.num_queries_vis_abstractor_video_fast
                        )
                        grid_idx = grid_idx + len(pixel_values_frame) - 1
                        num_grids.append(grid_idx)

        video_forward_outs = self.mm_projector(
            video_forward_outs, num_queries_vis_abstractors, num_grids
        )

        video_features = []  # what we want to return
        target_features = []
        target_group_size = 0
        group_counter = 0
        video_groups = [
            len(frame) for frames in pixel_values_videos for frame in frames
        ]  # for concat video features after projector

        for forward_out in video_forward_outs:
            target_group_size += len(forward_out)
            target_features.append(forward_out.flatten(0, 1))

            video_group_size = video_groups[group_counter]
            if video_group_size == target_group_size:
                video_features.append(torch.cat(target_features, dim=0))
                target_features = []
                group_counter += 1
                target_group_size = 0

            elif video_group_size < target_group_size:
                raise RuntimeError(f"{video_group_size=} < {target_group_size=}")

        assert len(target_features) == 0, (
            f"target_features is not empty!! {target_features}"
        )
        assert len(video_groups) == len(video_features)

        feats_per_video = [len(video) for video in pixel_values_videos]
        idxs_per_video = [0, *accumulate(feats_per_video)]
        return tuple(
            torch.cat(video_features[idxs_per_video[i] : idxs_per_video[i + 1]])
            for i in range(len(feats_per_video))
        )