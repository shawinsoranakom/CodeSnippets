def decode(self, samples_in, vae_options={}):
        self.throw_exception_if_invalid()
        pixel_samples = None
        do_tile = False
        if self.latent_dim == 2 and samples_in.ndim == 5:
            samples_in = samples_in[:, :, 0]
        try:
            memory_used = self.memory_used_decode(samples_in.shape, self.vae_dtype)
            model_management.load_models_gpu([self.patcher], memory_required=memory_used, force_full_load=self.disable_offload)
            free_memory = self.patcher.get_free_memory(self.device)
            batch_number = int(free_memory / memory_used)
            batch_number = max(1, batch_number)

            # Pre-allocate output for VAEs that support direct buffer writes
            preallocated = False
            if getattr(self.first_stage_model, 'comfy_has_chunked_io', False):
                pixel_samples = torch.empty(self.first_stage_model.decode_output_shape(samples_in.shape), device=self.output_device, dtype=self.vae_output_dtype())
                preallocated = True

            for x in range(0, samples_in.shape[0], batch_number):
                samples = samples_in[x:x + batch_number].to(device=self.device, dtype=self.vae_dtype)
                if preallocated:
                    self.first_stage_model.decode(samples, output_buffer=pixel_samples[x:x+batch_number], **vae_options)
                else:
                    out = self.first_stage_model.decode(samples, **vae_options).to(device=self.output_device, dtype=self.vae_output_dtype(), copy=True)
                    if pixel_samples is None:
                        pixel_samples = torch.empty((samples_in.shape[0],) + tuple(out.shape[1:]), device=self.output_device, dtype=self.vae_output_dtype())
                    pixel_samples[x:x+batch_number].copy_(out)
                    del out
                self.process_output(pixel_samples[x:x+batch_number])
        except Exception as e:
            model_management.raise_non_oom(e)
            logging.warning("Warning: Ran out of memory when regular VAE decoding, retrying with tiled VAE decoding.")
            #NOTE: We don't know what tensors were allocated to stack variables at the time of the
            #exception and the exception itself refs them all until we get out of this except block.
            #So we just set a flag for tiler fallback so that tensor gc can happen once the
            #exception is fully off the books.
            do_tile = True

        if do_tile:
            comfy.model_management.soft_empty_cache()
            dims = samples_in.ndim - 2
            if dims == 1 or self.extra_1d_channel is not None:
                pixel_samples = self.decode_tiled_1d(samples_in)
            elif dims == 2:
                pixel_samples = self.decode_tiled_(samples_in)
            elif dims == 3:
                tile = 256 // self.spacial_compression_decode()
                overlap = tile // 4
                pixel_samples = self.decode_tiled_3d(samples_in, tile_x=tile, tile_y=tile, overlap=(1, overlap, overlap))

        pixel_samples = pixel_samples.to(self.output_device).movedim(1,-1)
        return pixel_samples