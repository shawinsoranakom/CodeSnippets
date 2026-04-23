def encode_tiled(self, pixel_samples, tile_x=None, tile_y=None, overlap=None, tile_t=None, overlap_t=None):
        self.throw_exception_if_invalid()
        pixel_samples = self.vae_encode_crop_pixels(pixel_samples)
        dims = self.latent_dim
        pixel_samples = pixel_samples.movedim(-1, 1)
        if dims == 3:
            if not self.not_video:
                pixel_samples = pixel_samples.movedim(1, 0).unsqueeze(0)
            else:
                pixel_samples = pixel_samples.unsqueeze(2)

        memory_used = self.memory_used_encode(pixel_samples.shape, self.vae_dtype)  # TODO: calculate mem required for tile
        model_management.load_models_gpu([self.patcher], memory_required=memory_used, force_full_load=self.disable_offload)

        args = {}
        if tile_x is not None:
            args["tile_x"] = tile_x
        if tile_y is not None:
            args["tile_y"] = tile_y
        if overlap is not None:
            args["overlap"] = overlap

        if dims == 1:
            args.pop("tile_y")
            samples = self.encode_tiled_1d(pixel_samples, **args)
        elif dims == 2:
            samples = self.encode_tiled_(pixel_samples, **args)
        elif dims == 3:
            if tile_t is not None:
                tile_t_latent = max(2, self.downscale_ratio[0](tile_t))
            else:
                tile_t_latent = 9999
            args["tile_t"] = self.upscale_ratio[0](tile_t_latent)

            if overlap_t is None:
                args["overlap"] = (1, overlap, overlap)
            else:
                args["overlap"] = (self.upscale_ratio[0](max(1, min(tile_t_latent // 2, self.downscale_ratio[0](overlap_t)))), overlap, overlap)
            maximum = pixel_samples.shape[2]
            maximum = self.upscale_ratio[0](self.downscale_ratio[0](maximum))

            samples = self.encode_tiled_3d(pixel_samples[:,:,:maximum], **args)

        return samples