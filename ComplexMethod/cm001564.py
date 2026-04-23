def forward(self, x, sigma, uncond, cond, cond_scale, s_min_uncond, image_cond):
        if state.interrupted or state.skipped:
            raise sd_samplers_common.InterruptedException

        if sd_samplers_common.apply_refiner(self, sigma):
            cond = self.sampler.sampler_extra_args['cond']
            uncond = self.sampler.sampler_extra_args['uncond']

        # at self.image_cfg_scale == 1.0 produced results for edit model are the same as with normal sampling,
        # so is_edit_model is set to False to support AND composition.
        is_edit_model = shared.sd_model.cond_stage_key == "edit" and self.image_cfg_scale is not None and self.image_cfg_scale != 1.0

        conds_list, tensor = prompt_parser.reconstruct_multicond_batch(cond, self.step)
        uncond = prompt_parser.reconstruct_cond_batch(uncond, self.step)

        assert not is_edit_model or all(len(conds) == 1 for conds in conds_list), "AND is not supported for InstructPix2Pix checkpoint (unless using Image CFG scale = 1.0)"

        # If we use masks, blending between the denoised and original latent images occurs here.
        def apply_blend(current_latent):
            blended_latent = current_latent * self.nmask + self.init_latent * self.mask

            if self.p.scripts is not None:
                from modules import scripts
                mba = scripts.MaskBlendArgs(current_latent, self.nmask, self.init_latent, self.mask, blended_latent, denoiser=self, sigma=sigma)
                self.p.scripts.on_mask_blend(self.p, mba)
                blended_latent = mba.blended_latent

            return blended_latent

        # Blend in the original latents (before)
        if self.mask_before_denoising and self.mask is not None:
            x = apply_blend(x)

        batch_size = len(conds_list)
        repeats = [len(conds_list[i]) for i in range(batch_size)]

        if shared.sd_model.model.conditioning_key == "crossattn-adm":
            image_uncond = torch.zeros_like(image_cond)
            make_condition_dict = lambda c_crossattn, c_adm: {"c_crossattn": [c_crossattn], "c_adm": c_adm}
        else:
            image_uncond = image_cond
            if isinstance(uncond, dict):
                make_condition_dict = lambda c_crossattn, c_concat: {**c_crossattn, "c_concat": [c_concat]}
            else:
                make_condition_dict = lambda c_crossattn, c_concat: {"c_crossattn": [c_crossattn], "c_concat": [c_concat]}

        if not is_edit_model:
            x_in = torch.cat([torch.stack([x[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [x])
            sigma_in = torch.cat([torch.stack([sigma[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [sigma])
            image_cond_in = torch.cat([torch.stack([image_cond[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [image_uncond])
        else:
            x_in = torch.cat([torch.stack([x[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [x] + [x])
            sigma_in = torch.cat([torch.stack([sigma[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [sigma] + [sigma])
            image_cond_in = torch.cat([torch.stack([image_cond[i] for _ in range(n)]) for i, n in enumerate(repeats)] + [image_uncond] + [torch.zeros_like(self.init_latent)])

        denoiser_params = CFGDenoiserParams(x_in, image_cond_in, sigma_in, state.sampling_step, state.sampling_steps, tensor, uncond, self)
        cfg_denoiser_callback(denoiser_params)
        x_in = denoiser_params.x
        image_cond_in = denoiser_params.image_cond
        sigma_in = denoiser_params.sigma
        tensor = denoiser_params.text_cond
        uncond = denoiser_params.text_uncond
        skip_uncond = False

        if shared.opts.skip_early_cond != 0. and self.step / self.total_steps <= shared.opts.skip_early_cond:
            skip_uncond = True
            self.p.extra_generation_params["Skip Early CFG"] = shared.opts.skip_early_cond
        elif (self.step % 2 or shared.opts.s_min_uncond_all) and s_min_uncond > 0 and sigma[0] < s_min_uncond and not is_edit_model:
            skip_uncond = True
            self.p.extra_generation_params["NGMS"] = s_min_uncond
            if shared.opts.s_min_uncond_all:
                self.p.extra_generation_params["NGMS all steps"] = shared.opts.s_min_uncond_all

        if skip_uncond:
            x_in = x_in[:-batch_size]
            sigma_in = sigma_in[:-batch_size]

        self.padded_cond_uncond = False
        self.padded_cond_uncond_v0 = False
        if shared.opts.pad_cond_uncond_v0 and tensor.shape[1] != uncond.shape[1]:
            tensor, uncond = self.pad_cond_uncond_v0(tensor, uncond)
        elif shared.opts.pad_cond_uncond and tensor.shape[1] != uncond.shape[1]:
            tensor, uncond = self.pad_cond_uncond(tensor, uncond)

        if tensor.shape[1] == uncond.shape[1] or skip_uncond:
            if is_edit_model:
                cond_in = catenate_conds([tensor, uncond, uncond])
            elif skip_uncond:
                cond_in = tensor
            else:
                cond_in = catenate_conds([tensor, uncond])

            if shared.opts.batch_cond_uncond:
                x_out = self.inner_model(x_in, sigma_in, cond=make_condition_dict(cond_in, image_cond_in))
            else:
                x_out = torch.zeros_like(x_in)
                for batch_offset in range(0, x_out.shape[0], batch_size):
                    a = batch_offset
                    b = a + batch_size
                    x_out[a:b] = self.inner_model(x_in[a:b], sigma_in[a:b], cond=make_condition_dict(subscript_cond(cond_in, a, b), image_cond_in[a:b]))
        else:
            x_out = torch.zeros_like(x_in)
            batch_size = batch_size*2 if shared.opts.batch_cond_uncond else batch_size
            for batch_offset in range(0, tensor.shape[0], batch_size):
                a = batch_offset
                b = min(a + batch_size, tensor.shape[0])

                if not is_edit_model:
                    c_crossattn = subscript_cond(tensor, a, b)
                else:
                    c_crossattn = torch.cat([tensor[a:b]], uncond)

                x_out[a:b] = self.inner_model(x_in[a:b], sigma_in[a:b], cond=make_condition_dict(c_crossattn, image_cond_in[a:b]))

            if not skip_uncond:
                x_out[-uncond.shape[0]:] = self.inner_model(x_in[-uncond.shape[0]:], sigma_in[-uncond.shape[0]:], cond=make_condition_dict(uncond, image_cond_in[-uncond.shape[0]:]))

        denoised_image_indexes = [x[0][0] for x in conds_list]
        if skip_uncond:
            fake_uncond = torch.cat([x_out[i:i+1] for i in denoised_image_indexes])
            x_out = torch.cat([x_out, fake_uncond])  # we skipped uncond denoising, so we put cond-denoised image to where the uncond-denoised image should be

        denoised_params = CFGDenoisedParams(x_out, state.sampling_step, state.sampling_steps, self.inner_model)
        cfg_denoised_callback(denoised_params)

        if self.need_last_noise_uncond:
            self.last_noise_uncond = torch.clone(x_out[-uncond.shape[0]:])

        if is_edit_model:
            denoised = self.combine_denoised_for_edit_model(x_out, cond_scale * self.cond_scale_miltiplier)
        elif skip_uncond:
            denoised = self.combine_denoised(x_out, conds_list, uncond, 1.0)
        else:
            denoised = self.combine_denoised(x_out, conds_list, uncond, cond_scale * self.cond_scale_miltiplier)

        # Blend in the original latents (after)
        if not self.mask_before_denoising and self.mask is not None:
            denoised = apply_blend(denoised)

        self.sampler.last_latent = self.get_pred_x0(torch.cat([x_in[i:i + 1] for i in denoised_image_indexes]), torch.cat([x_out[i:i + 1] for i in denoised_image_indexes]), sigma)

        if opts.live_preview_content == "Prompt":
            preview = self.sampler.last_latent
        elif opts.live_preview_content == "Negative prompt":
            preview = self.get_pred_x0(x_in[-uncond.shape[0]:], x_out[-uncond.shape[0]:], sigma)
        else:
            preview = self.get_pred_x0(torch.cat([x_in[i:i+1] for i in denoised_image_indexes]), torch.cat([denoised[i:i+1] for i in denoised_image_indexes]), sigma)

        sd_samplers_common.store_latent(preview)

        after_cfg_callback_params = AfterCFGCallbackParams(denoised, state.sampling_step, state.sampling_steps)
        cfg_after_cfg_callback(after_cfg_callback_params)
        denoised = after_cfg_callback_params.x

        self.step += 1
        return denoised