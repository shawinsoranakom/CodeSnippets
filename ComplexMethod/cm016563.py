def encode(self, pixel_samples):
        self.throw_exception_if_invalid()
        pixel_samples = self.vae_encode_crop_pixels(pixel_samples)
        pixel_samples = pixel_samples.movedim(-1, 1)
        do_tile = False
        if self.latent_dim == 3 and pixel_samples.ndim < 5:
            if not self.not_video:
                pixel_samples = pixel_samples.movedim(1, 0).unsqueeze(0)
            else:
                pixel_samples = pixel_samples.unsqueeze(2)
        try:
            memory_used = self.memory_used_encode(pixel_samples.shape, self.vae_dtype)
            model_management.load_models_gpu([self.patcher], memory_required=memory_used, force_full_load=self.disable_offload)
            free_memory = self.patcher.get_free_memory(self.device)
            batch_number = int(free_memory / max(1, memory_used))
            batch_number = max(1, batch_number)
            samples = None
            for x in range(0, pixel_samples.shape[0], batch_number):
                pixels_in = self.process_input(pixel_samples[x:x + batch_number]).to(self.vae_dtype)
                if getattr(self.first_stage_model, 'comfy_has_chunked_io', False):
                    out = self.first_stage_model.encode(pixels_in, device=self.device)
                else:
                    pixels_in = pixels_in.to(self.device)
                    out = self.first_stage_model.encode(pixels_in)
                out = out.to(self.output_device).to(dtype=self.vae_output_dtype())
                if samples is None:
                    samples = torch.empty((pixel_samples.shape[0],) + tuple(out.shape[1:]), device=self.output_device, dtype=self.vae_output_dtype())
                samples[x:x + batch_number] = out

        except Exception as e:
            model_management.raise_non_oom(e)
            logging.warning("Warning: Ran out of memory when regular VAE encoding, retrying with tiled VAE encoding.")
            #NOTE: We don't know what tensors were allocated to stack variables at the time of the
            #exception and the exception itself refs them all until we get out of this except block.
            #So we just set a flag for tiler fallback so that tensor gc can happen once the
            #exception is fully off the books.
            do_tile = True

        if do_tile:
            comfy.model_management.soft_empty_cache()
            if self.latent_dim == 3:
                tile = 256
                overlap = tile // 4
                samples = self.encode_tiled_3d(pixel_samples, tile_x=tile, tile_y=tile, overlap=(1, overlap, overlap))
            elif self.latent_dim == 1 or self.extra_1d_channel is not None:
                samples = self.encode_tiled_1d(pixel_samples)
            else:
                samples = self.encode_tiled_(pixel_samples)

        return samples