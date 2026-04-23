def extra_conds(self, **kwargs):
        out = super().extra_conds(**kwargs)
        attention_mask = kwargs.get("attention_mask", None)
        if attention_mask is not None:
            if torch.numel(attention_mask) != attention_mask.sum():
                out['attention_mask'] = comfy.conds.CONDRegular(attention_mask)
            out['num_tokens'] = comfy.conds.CONDConstant(max(1, torch.sum(attention_mask).item()))

        cross_attn = kwargs.get("cross_attn", None)
        if cross_attn is not None:
            out['c_crossattn'] = comfy.conds.CONDRegular(cross_attn)
            if 'num_tokens' not in out:
                out['num_tokens'] = comfy.conds.CONDConstant(cross_attn.shape[1])

        clip_text_pooled = kwargs.get("pooled_output", None)  # NewBie
        if clip_text_pooled is not None:
            out['clip_text_pooled'] = comfy.conds.CONDRegular(clip_text_pooled)

        clip_vision_outputs = kwargs.get("clip_vision_outputs", list(map(lambda a: a.get("clip_vision_output"), kwargs.get("unclip_conditioning", [{}]))))  # Z Image omni
        if clip_vision_outputs is not None and len(clip_vision_outputs) > 0:
            sigfeats = []
            for clip_vision_output in clip_vision_outputs:
                if clip_vision_output is not None:
                    image_size = clip_vision_output.image_sizes[0]
                    shape = clip_vision_output.last_hidden_state.shape
                    sigfeats.append(clip_vision_output.last_hidden_state.reshape(shape[0], image_size[1] // 16, image_size[2] // 16, shape[-1]))
            if len(sigfeats) > 0:
                out['siglip_feats'] = comfy.conds.CONDList(sigfeats)

        ref_latents = kwargs.get("reference_latents", None)
        if ref_latents is not None:
            latents = []
            for lat in ref_latents:
                latents.append(self.process_latent_in(lat))
            out['ref_latents'] = comfy.conds.CONDList(latents)

        ref_contexts = kwargs.get("reference_latents_text_embeds", None)
        if ref_contexts is not None:
            out['ref_contexts'] = comfy.conds.CONDList(ref_contexts)

        return out