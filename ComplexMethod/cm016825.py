def execute(cls, positive, negative, vae, tracks, width, height, length, batch_size,
               temperature, topk, start_image=None, clip_vision_output=None) -> io.NodeOutput:

        tracks_data = parse_json_tracks(tracks)

        if not tracks_data:
            return WanImageToVideo().execute(positive, negative, vae, width, height, length, batch_size, start_image=start_image, clip_vision_output=clip_vision_output)

        latent = torch.zeros([batch_size, 16, ((length - 1) // 4) + 1, height // 8, width // 8],
                           device=comfy.model_management.intermediate_device())

        if isinstance(tracks_data[0][0], dict):
            tracks_data = [tracks_data]

        processed_tracks = []
        for batch in tracks_data:
            arrs = []
            for track in batch:
                pts = pad_pts(track)
                arrs.append(pts)

            tracks_np = np.stack(arrs, axis=0)
            processed_tracks.append(process_tracks(tracks_np, (width, height), length - 1).unsqueeze(0))

        if start_image is not None:
            start_image = comfy.utils.common_upscale(start_image[:batch_size].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            videos = torch.ones((start_image.shape[0], length, height, width, start_image.shape[-1]), device=start_image.device, dtype=start_image.dtype) * 0.5
            for i in range(start_image.shape[0]):
                videos[i, 0] = start_image[i]

            latent_videos = []
            videos = comfy.utils.resize_to_batch_size(videos, batch_size)
            for i in range(batch_size):
                latent_videos += [vae.encode(videos[i, :, :, :, :3])]
            y = torch.cat(latent_videos, dim=0)

            # Scale latent since patch_motion is non-linear
            y = comfy.latent_formats.Wan21().process_in(y)

            processed_tracks = comfy.utils.resize_list_to_batch_size(processed_tracks, batch_size)
            res = patch_motion(
                processed_tracks, y, temperature=temperature, topk=topk, vae_divide=(4, 16)
            )

            mask, concat_latent_image = res
            concat_latent_image = comfy.latent_formats.Wan21().process_out(concat_latent_image)
            mask = -mask + 1.0  # Invert mask to match expected format
            positive = node_helpers.conditioning_set_values(positive,
                                                            {"concat_mask": mask,
                                                            "concat_latent_image": concat_latent_image})
            negative = node_helpers.conditioning_set_values(negative,
                                                            {"concat_mask": mask,
                                                            "concat_latent_image": concat_latent_image})

        if clip_vision_output is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_output})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_output})

        out_latent = {}
        out_latent["samples"] = latent
        return io.NodeOutput(positive, negative, out_latent)