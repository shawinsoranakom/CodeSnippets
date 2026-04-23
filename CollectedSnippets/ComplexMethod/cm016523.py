def extra_conds(self, **kwargs):
        out = super().extra_conds(**kwargs)
        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            out['c_crossattn'] = comfy.conds.CONDRegular(cross_attn)
        # upscale the attention mask, since now we
        attention_mask = kwargs.get("attention_mask", None)
        if attention_mask is not None:
            shape = kwargs["noise"].shape
            mask_ref_size = kwargs.get("attention_mask_img_shape", None)
            if mask_ref_size is not None:
                # the model will pad to the patch size, and then divide
                # essentially dividing and rounding up
                (h_tok, w_tok) = (math.ceil(shape[2] / self.diffusion_model.patch_size), math.ceil(shape[3] / self.diffusion_model.patch_size))
                attention_mask = utils.upscale_dit_mask(attention_mask, mask_ref_size, (h_tok, w_tok))
                out['attention_mask'] = comfy.conds.CONDRegular(attention_mask)

        guidance = kwargs.get("guidance", 3.5)
        if guidance is not None:
            out['guidance'] = comfy.conds.CONDRegular(torch.FloatTensor([guidance]))

        ref_latents = kwargs.get("reference_latents", None)
        if ref_latents is not None:
            latents = []
            for lat in ref_latents:
                latents.append(self.process_latent_in(lat))
            out['ref_latents'] = comfy.conds.CONDList(latents)

            ref_latents_method = kwargs.get("reference_latents_method", None)
            if ref_latents_method is not None:
                out['ref_latents_method'] = comfy.conds.CONDConstant(ref_latents_method)
        return out