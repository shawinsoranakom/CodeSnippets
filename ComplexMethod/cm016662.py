def forward_orig(self, x, timestep, y, mask=None, c_size=None, c_ar=None, **kwargs):
        """
        Original forward pass of PixArt.
        x: (N, C, H, W) tensor of spatial inputs (images or latent representations of images)
        t: (N,) tensor of diffusion timesteps
        y: (N, 1, 120, C) conditioning
        ar: (N, 1): aspect ratio
        cs: (N ,2) size conditioning for height/width
        """
        B, C, H, W = x.shape
        c_res = (H + W) // 2
        pe_interpolation = self.pe_interpolation
        if pe_interpolation is None or self.pe_precision is not None:
            # calculate pe_interpolation on-the-fly
            pe_interpolation = round(c_res / (512/8.0), self.pe_precision or 0)

        pos_embed = get_2d_sincos_pos_embed_torch(
            self.hidden_size,
            h=(H // self.patch_size),
            w=(W // self.patch_size),
            pe_interpolation=pe_interpolation,
            base_size=((round(c_res / 64) * 64) // self.patch_size),
            device=x.device,
            dtype=x.dtype,
        ).unsqueeze(0)

        x = self.x_embedder(x) + pos_embed  # (N, T, D), where T = H * W / patch_size ** 2
        t = self.t_embedder(timestep, x.dtype)  # (N, D)

        if self.micro_conditioning and (c_size is not None and c_ar is not None):
            bs = x.shape[0]
            c_size = self.csize_embedder(c_size, bs)  # (N, D)
            c_ar = self.ar_embedder(c_ar, bs)  # (N, D)
            t = t + torch.cat([c_size, c_ar], dim=1)

        t0 = self.t_block(t)
        y = self.y_embedder(y, self.training)  # (N, D)

        if mask is not None:
            if mask.shape[0] != y.shape[0]:
                mask = mask.repeat(y.shape[0] // mask.shape[0], 1)
            mask = mask.squeeze(1).squeeze(1)
            y = y.squeeze(1).masked_select(mask.unsqueeze(-1) != 0).view(1, -1, x.shape[-1])
            y_lens = mask.sum(dim=1).tolist()
        else:
            y_lens = None
            y = y.squeeze(1).view(1, -1, x.shape[-1])
        for block in self.blocks:
            x = block(x, y, t0, y_lens, (H, W), **kwargs)  # (N, T, D)

        x = self.final_layer(x, t)  # (N, T, patch_size ** 2 * out_channels)
        x = self.unpatchify(x, H, W)  # (N, out_channels, H, W)

        return x