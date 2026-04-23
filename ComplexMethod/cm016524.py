def extra_conds(self, **kwargs):
        out = super().extra_conds(**kwargs)
        attention_mask = kwargs.get("attention_mask", None)
        device = kwargs["device"]

        if attention_mask is not None:
            out['attention_mask'] = comfy.conds.CONDRegular(attention_mask)
        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            if hasattr(self.diffusion_model, "preprocess_text_embeds"):
                cross_attn = self.diffusion_model.preprocess_text_embeds(cross_attn.to(device=device, dtype=self.get_dtype_inference()), unprocessed=kwargs.get("unprocessed_ltxav_embeds", False))
            out['c_crossattn'] = comfy.conds.CONDRegular(cross_attn)

        out['frame_rate'] = comfy.conds.CONDConstant(kwargs.get("frame_rate", 25))

        denoise_mask = kwargs.get("concat_mask", kwargs.get("denoise_mask", None))

        audio_denoise_mask = None
        if denoise_mask is not None and "latent_shapes" in kwargs:
            denoise_mask = utils.unpack_latents(denoise_mask, kwargs["latent_shapes"])
            if len(denoise_mask) > 1:
                audio_denoise_mask = denoise_mask[1]
            denoise_mask = denoise_mask[0]

        if denoise_mask is not None:
            out["denoise_mask"] = comfy.conds.CONDRegular(denoise_mask)

        if audio_denoise_mask is not None:
            out["audio_denoise_mask"] = comfy.conds.CONDRegular(audio_denoise_mask)

        keyframe_idxs = kwargs.get("keyframe_idxs", None)
        if keyframe_idxs is not None:
            out['keyframe_idxs'] = comfy.conds.CONDRegular(keyframe_idxs)

        latent_shapes = kwargs.get("latent_shapes", None)
        if latent_shapes is not None:
            out['latent_shapes'] = comfy.conds.CONDConstant(latent_shapes)

        guide_attention_entries = kwargs.get("guide_attention_entries", None)
        if guide_attention_entries is not None:
            out['guide_attention_entries'] = comfy.conds.CONDConstant(guide_attention_entries)

        ref_audio = kwargs.get("ref_audio", None)
        if ref_audio is not None:
            out['ref_audio'] = comfy.conds.CONDConstant(ref_audio)

        return out