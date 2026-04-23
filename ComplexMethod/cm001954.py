def expected_output_video_shape(self, videos):
        grid_t = self.num_frames
        hidden_dim = self.num_channels * self.patch_size * self.patch_size
        seq_len = 0
        for video in videos:
            if isinstance(video, list) and isinstance(video[0], Image.Image):
                video = np.stack([np.array(frame) for frame in video])
            elif hasattr(video, "shape"):
                pass
            else:
                video = np.array(video)

            if hasattr(video, "shape") and len(video.shape) >= 3:
                if len(video.shape) == 4:
                    _, height, width = video.shape[:3]
                elif len(video.shape) == 3:
                    height, width = video.shape[:2]
                else:
                    height, width = self.num_frames, self.min_resolution, self.min_resolution
            else:
                height, width = self.min_resolution, self.min_resolution

            resized_height, resized_width = smart_resize(
                height,
                width,
                factor=self.patch_size * self.merge_size,
                min_pixels=self.size["shortest_edge"],
                max_pixels=self.size["longest_edge"],
            )
            grid_h, grid_w = resized_height // self.patch_size, resized_width // self.patch_size
            seq_len += grid_t * grid_h * grid_w
        return [seq_len, hidden_dim]