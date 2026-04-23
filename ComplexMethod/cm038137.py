def _parse_and_validate_video_input(
        self, **kwargs: object
    ) -> NanoNemotronVLVideoPixelInputs | None:
        pixel_values_flat_video = kwargs.pop("pixel_values_flat_video", None)
        video_num_patches = kwargs.pop("video_num_patches", None)
        video_embeds = kwargs.pop("video_embeds", None)
        frames_indices = kwargs.pop("frames_indices", None)
        frame_duration_ms = kwargs.pop("frame_duration_ms", None)

        if pixel_values_flat_video is None and video_embeds is None:
            return None

        if video_embeds is not None:
            return NanoNemotronVLVideoEmbeddingInputs(
                type="video_embeds",
                data=video_embeds,
            )

        if pixel_values_flat_video is not None:
            if torch.is_tensor(frames_indices):
                frames_indices = frames_indices.flatten()
            else:
                frames_indices = torch.cat([f.flatten() for f in frames_indices], dim=0)

            if torch.is_tensor(frame_duration_ms):
                frame_duration_ms = frame_duration_ms.flatten()
            else:
                frame_duration_ms = torch.cat(
                    [f.flatten() for f in frame_duration_ms], dim=0
                )

            if (
                torch.is_tensor(pixel_values_flat_video)
                and pixel_values_flat_video.ndim == 5
            ):
                # batched._reduce_data stacked same-shape videos into
                # [num_videos, nf, 3, H, W]; unstack back to a list so the
                # same-H,W cat path below handles it uniformly.
                pixel_values_flat_video = list(pixel_values_flat_video)

            if not torch.is_tensor(pixel_values_flat_video):
                pixel_values_flat_video = torch.cat(pixel_values_flat_video, dim=0)

            expected_h = pixel_values_flat_video.shape[-2]
            expected_w = pixel_values_flat_video.shape[-1]
            num_frames = video_num_patches[0].item()
            resolve_bindings = {"h": expected_h, "w": expected_w, "f": num_frames}

            return NanoNemotronVLVideoPixelInputs(
                type="pixel_values_videos",
                pixel_values_flat=pixel_values_flat_video,
                num_patches=video_num_patches,
                frames_indices=frames_indices,
                frame_duration_ms=frame_duration_ms,
                resolve_bindings=resolve_bindings,
            )

        raise AssertionError("This line should be unreachable.")