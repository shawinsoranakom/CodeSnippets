def _apply_model(self, x, t, c_concat=None, c_crossattn=None, control=None, transformer_options={}, **kwargs):
        sigma = t
        xc = self.model_sampling.calculate_input(sigma, x)

        if c_concat is not None:
            xc = torch.cat([xc] + [comfy.model_management.cast_to_device(c_concat, xc.device, xc.dtype)], dim=1)

        context = c_crossattn
        dtype = self.get_dtype_inference()

        xc = xc.to(dtype)
        device = xc.device
        t = self.model_sampling.timestep(t).float()
        if context is not None:
            context = comfy.model_management.cast_to_device(context, device, dtype)

        extra_conds = {}
        for o in kwargs:
            extra = kwargs[o]

            if hasattr(extra, "dtype"):
                extra = convert_tensor(extra, dtype, device)
            elif isinstance(extra, list):
                ex = []
                for ext in extra:
                    ex.append(convert_tensor(ext, dtype, device))
                extra = ex
            extra_conds[o] = extra

        t = self.process_timestep(t, x=x, **extra_conds)
        if "latent_shapes" in extra_conds:
            xc = utils.unpack_latents(xc, extra_conds.pop("latent_shapes"))

        model_output = self.diffusion_model(xc, t, context=context, control=control, transformer_options=transformer_options, **extra_conds)
        if len(model_output) > 1 and not torch.is_tensor(model_output):
            model_output, _ = utils.pack_latents(model_output)

        return self.model_sampling.calculate_denoised(sigma, model_output.float(), x)