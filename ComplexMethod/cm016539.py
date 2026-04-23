def sample(self, noise, latent_image, sampler, sigmas, denoise_mask=None, callback=None, disable_pbar=False, seed=None):
        if sigmas.shape[-1] == 0:
            return latent_image

        if latent_image.is_nested:
            latent_image, latent_shapes = comfy.utils.pack_latents(latent_image.unbind())
            noise, _ = comfy.utils.pack_latents(noise.unbind())
        else:
            latent_shapes = [latent_image.shape]

        if denoise_mask is not None:
            if denoise_mask.is_nested:
                denoise_masks = denoise_mask.unbind()
                denoise_masks = denoise_masks[:len(latent_shapes)]
            else:
                denoise_masks = [denoise_mask]

            for i in range(len(denoise_masks), len(latent_shapes)):
                denoise_masks.append(torch.ones(latent_shapes[i]))

            for i in range(len(denoise_masks)):
                denoise_masks[i] = comfy.sampler_helpers.prepare_mask(denoise_masks[i], latent_shapes[i], self.model_patcher.load_device)

            if len(denoise_masks) > 1:
                denoise_mask, _ = comfy.utils.pack_latents(denoise_masks)
            else:
                denoise_mask = denoise_masks[0]
            denoise_mask = denoise_mask.float()

        self.conds = {}
        for k in self.original_conds:
            self.conds[k] = list(map(lambda a: a.copy(), self.original_conds[k]))
        preprocess_conds_hooks(self.conds)

        try:
            orig_model_options = self.model_options
            self.model_options = comfy.model_patcher.create_model_options_clone(self.model_options)
            # if one hook type (or just None), then don't bother caching weights for hooks (will never change after first step)
            orig_hook_mode = self.model_patcher.hook_mode
            if get_total_hook_groups_in_conds(self.conds) <= 1:
                self.model_patcher.hook_mode = comfy.hooks.EnumHookMode.MinVram
            comfy.sampler_helpers.prepare_model_patcher(self.model_patcher, self.conds, self.model_options)
            filter_registered_hooks_on_conds(self.conds, self.model_options)
            executor = comfy.patcher_extension.WrapperExecutor.new_class_executor(
                self.outer_sample,
                self,
                comfy.patcher_extension.get_all_wrappers(comfy.patcher_extension.WrappersMP.OUTER_SAMPLE, self.model_options, is_model_options=True)
            )
            output = executor.execute(noise, latent_image, sampler, sigmas, denoise_mask, callback, disable_pbar, seed, latent_shapes=latent_shapes)
        finally:
            cast_to_load_options(self.model_options, device=self.model_patcher.offload_device)
            self.model_options = orig_model_options
            self.model_patcher.hook_mode = orig_hook_mode
            self.model_patcher.restore_hook_patches()

        del self.conds

        if len(latent_shapes) > 1:
            output = comfy.nested_tensor.NestedTensor(comfy.utils.unpack_latents(output, latent_shapes))
        return output