def get_control(self, x_noisy, t, cond, batched_number, transformer_options):
        control_prev = None
        if self.previous_controlnet is not None:
            control_prev = self.previous_controlnet.get_control(x_noisy, t, cond, batched_number, transformer_options)

        if self.timestep_range is not None:
            if t[0] > self.timestep_range[0] or t[0] < self.timestep_range[1]:
                if control_prev is not None:
                    return control_prev
                else:
                    return None

        dtype = self.control_model.dtype
        if self.manual_cast_dtype is not None:
            dtype = self.manual_cast_dtype

        if self.cond_hint is None or x_noisy.shape[2] * self.compression_ratio != self.cond_hint.shape[2] or x_noisy.shape[3] * self.compression_ratio != self.cond_hint.shape[3]:
            if self.cond_hint is not None:
                del self.cond_hint
            self.cond_hint = None
            compression_ratio = self.compression_ratio
            if self.vae is not None:
                compression_ratio *= self.vae.spacial_compression_encode()
            else:
                if self.latent_format is not None:
                    raise ValueError("This Controlnet needs a VAE but none was provided, please use a ControlNetApply node with a VAE input and connect it.")
            self.cond_hint = comfy.utils.common_upscale(self.cond_hint_original, x_noisy.shape[-1] * compression_ratio, x_noisy.shape[-2] * compression_ratio, self.upscale_algorithm, "center")
            self.cond_hint = self.preprocess_image(self.cond_hint)
            if self.vae is not None:
                loaded_models = comfy.model_management.loaded_models(only_currently_used=True)
                self.cond_hint = self.vae.encode(self.cond_hint.movedim(1, -1))
                comfy.model_management.load_models_gpu(loaded_models)
            if self.latent_format is not None:
                self.cond_hint = self.latent_format.process_in(self.cond_hint)
            if len(self.extra_concat_orig) > 0:
                to_concat = []
                for c in self.extra_concat_orig:
                    c = c.to(self.cond_hint.device)
                    c = comfy.utils.common_upscale(c, self.cond_hint.shape[-1], self.cond_hint.shape[-2], self.upscale_algorithm, "center")
                    if c.ndim < self.cond_hint.ndim:
                        c = c.unsqueeze(2)
                        c = comfy.utils.repeat_to_batch_size(c, self.cond_hint.shape[2], dim=2)
                    to_concat.append(comfy.utils.repeat_to_batch_size(c, self.cond_hint.shape[0]))
                self.cond_hint = torch.cat([self.cond_hint] + to_concat, dim=1)

            self.cond_hint = self.cond_hint.to(device=x_noisy.device, dtype=dtype)
        if x_noisy.shape[0] != self.cond_hint.shape[0]:
            self.cond_hint = broadcast_image_to(self.cond_hint, x_noisy.shape[0], batched_number)

        context = cond.get('crossattn_controlnet', cond['c_crossattn'])
        extra = self.extra_args.copy()
        for c in self.extra_conds:
            temp = cond.get(c, None)
            if temp is not None:
                extra[c] = comfy.model_base.convert_tensor(temp, dtype, x_noisy.device)

        timestep = self.model_sampling_current.timestep(t)
        x_noisy = self.model_sampling_current.calculate_input(t, x_noisy)

        control = self.control_model(x=x_noisy.to(dtype), hint=self.cond_hint, timesteps=timestep.to(dtype), context=comfy.model_management.cast_to_device(context, x_noisy.device, dtype), **extra)
        return self.control_merge(control, control_prev, output_dtype=None)