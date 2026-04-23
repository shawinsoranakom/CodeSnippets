def forward(self, motion_latents, rope_embedder, add_last_motion=2):
        lat_height, lat_width = motion_latents.shape[3], motion_latents.shape[4]
        padd_lat = torch.zeros(motion_latents.shape[0], 16, sum(self.zip_frame_buckets), lat_height, lat_width).to(device=motion_latents.device, dtype=motion_latents.dtype)
        overlap_frame = min(padd_lat.shape[2], motion_latents.shape[2])
        if overlap_frame > 0:
            padd_lat[:, :, -overlap_frame:] = motion_latents[:, :, -overlap_frame:]

        if add_last_motion < 2 and self.drop_mode != "drop":
            zero_end_frame = sum(self.zip_frame_buckets[:len(self.zip_frame_buckets) - add_last_motion - 1])
            padd_lat[:, :, -zero_end_frame:] = 0

        clean_latents_4x, clean_latents_2x, clean_latents_post = padd_lat[:, :, -sum(self.zip_frame_buckets):, :, :].split(self.zip_frame_buckets[::-1], dim=2)  # 16, 2 ,1

        # patchfy
        clean_latents_post = self.proj(clean_latents_post).flatten(2).transpose(1, 2)
        clean_latents_2x = self.proj_2x(clean_latents_2x)
        l_2x_shape = clean_latents_2x.shape
        clean_latents_2x = clean_latents_2x.flatten(2).transpose(1, 2)
        clean_latents_4x = self.proj_4x(clean_latents_4x)
        l_4x_shape = clean_latents_4x.shape
        clean_latents_4x = clean_latents_4x.flatten(2).transpose(1, 2)

        if add_last_motion < 2 and self.drop_mode == "drop":
            clean_latents_post = clean_latents_post[:, :
                                                    0] if add_last_motion < 2 else clean_latents_post
            clean_latents_2x = clean_latents_2x[:, :
                                                0] if add_last_motion < 1 else clean_latents_2x

        motion_lat = torch.cat([clean_latents_post, clean_latents_2x, clean_latents_4x], dim=1)

        rope_post = rope_embedder.rope_encode(1, lat_height, lat_width, t_start=-1, device=motion_latents.device, dtype=motion_latents.dtype)
        rope_2x = rope_embedder.rope_encode(1, lat_height, lat_width, t_start=-3, steps_h=l_2x_shape[-2], steps_w=l_2x_shape[-1], device=motion_latents.device, dtype=motion_latents.dtype)
        rope_4x = rope_embedder.rope_encode(4, lat_height, lat_width, t_start=-19, steps_h=l_4x_shape[-2], steps_w=l_4x_shape[-1], device=motion_latents.device, dtype=motion_latents.dtype)

        rope = torch.cat([rope_post, rope_2x, rope_4x], dim=1)
        return motion_lat, rope