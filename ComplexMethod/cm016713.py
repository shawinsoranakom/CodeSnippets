def patchify_and_embed(
        self, x: torch.Tensor, cap_feats: torch.Tensor, cap_mask: torch.Tensor, t: torch.Tensor, num_tokens, ref_latents=[], ref_contexts=[], siglip_feats=[], transformer_options={}
    ) -> Tuple[torch.Tensor, torch.Tensor, List[Tuple[int, int]], List[int], torch.Tensor]:
        bsz = x.shape[0]
        cap_mask = None  # TODO?
        main_siglip = None
        orig_x = x

        embeds = ([], [], [])
        freqs_cis = ([], [], [])
        leftover_cap = []

        start_t = 0
        omni = len(ref_latents) > 0
        if omni:
            for i, ref in enumerate(ref_latents):
                if i < len(ref_contexts):
                    ref_con = ref_contexts[i]
                else:
                    ref_con = None
                if i < len(siglip_feats):
                    sig_feat = siglip_feats[i]
                else:
                    sig_feat = None

                out = self.embed_all(ref, ref_con, sig_feat, offset=start_t, omni=omni, transformer_options=transformer_options)
                for i, e in enumerate(out[0]):
                    if e is not None:
                        embeds[i].append(comfy.utils.repeat_to_batch_size(e, bsz))
                        freqs_cis[i].append(out[1][i])
                start_t = out[2]
            leftover_cap = ref_contexts[len(ref_latents):]

        H, W = x.shape[-2], x.shape[-1]
        img_sizes = [(H, W)] * bsz
        out = self.embed_all(x, cap_feats, main_siglip, offset=start_t, omni=omni, transformer_options=transformer_options)
        img_len = out[0][-1].shape[1]
        cap_len = out[0][0].shape[1]
        for i, e in enumerate(out[0]):
            if e is not None:
                e = comfy.utils.repeat_to_batch_size(e, bsz)
                embeds[i].append(e)
                freqs_cis[i].append(out[1][i])
        start_t = out[2]

        for cap in leftover_cap:
            out = self.embed_cap(cap, offset=start_t, bsz=bsz, device=x.device, dtype=x.dtype)
            cap_len += out[0][0].shape[1]
            embeds[0].append(comfy.utils.repeat_to_batch_size(out[0][0], bsz))
            freqs_cis[0].append(out[1][0])
            start_t += out[2]

        patches = transformer_options.get("patches", {})

        # refine context
        cap_feats = torch.cat(embeds[0], dim=1)
        cap_freqs_cis = torch.cat(freqs_cis[0], dim=1)
        for layer in self.context_refiner:
            cap_feats = layer(cap_feats, cap_mask, cap_freqs_cis, transformer_options=transformer_options)

        feats = (cap_feats,)
        fc = (cap_freqs_cis,)

        if omni and len(embeds[1]) > 0:
            siglip_mask = None
            siglip_feats_combined = torch.cat(embeds[1], dim=1)
            siglip_feats_freqs_cis = torch.cat(freqs_cis[1], dim=1)
            if self.siglip_refiner is not None:
                for layer in self.siglip_refiner:
                    siglip_feats_combined = layer(siglip_feats_combined, siglip_mask, siglip_feats_freqs_cis, transformer_options=transformer_options)
            feats += (siglip_feats_combined,)
            fc += (siglip_feats_freqs_cis,)

        padded_img_mask = None
        x = torch.cat(embeds[-1], dim=1)
        fc_x = torch.cat(freqs_cis[-1], dim=1)
        if omni:
            timestep_zero_index = [(x.shape[1] - img_len, x.shape[1])]
        else:
            timestep_zero_index = None

        x_input = x
        for i, layer in enumerate(self.noise_refiner):
            x = layer(x, padded_img_mask, fc_x, t, timestep_zero_index=timestep_zero_index, transformer_options=transformer_options)
            if "noise_refiner" in patches:
                for p in patches["noise_refiner"]:
                    out = p({"img": x, "img_input": x_input, "txt": cap_feats, "pe": fc_x, "vec": t, "x": orig_x, "block_index": i, "transformer_options": transformer_options, "block_type": "noise_refiner"})
                    if "img" in out:
                        x = out["img"]

        padded_full_embed = torch.cat(feats + (x,), dim=1)
        if timestep_zero_index is not None:
            ind = padded_full_embed.shape[1] - x.shape[1]
            timestep_zero_index = [(ind + x.shape[1] - img_len, ind + x.shape[1])]
            timestep_zero_index.append((feats[0].shape[1] - cap_len, feats[0].shape[1]))

        mask = None
        l_effective_cap_len = [padded_full_embed.shape[1] - img_len] * bsz
        return padded_full_embed, mask, img_sizes, l_effective_cap_len, torch.cat(fc + (fc_x,), dim=1), timestep_zero_index