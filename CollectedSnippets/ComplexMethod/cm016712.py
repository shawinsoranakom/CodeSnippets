def embed_all(self, x, cap_feats=None, siglip_feats=None, offset=0, omni=False, transformer_options={}):
        bsz = 1
        pH = pW = self.patch_size
        device = x.device
        embeds, freqs_cis, cap_feats_len = self.embed_cap(cap_feats, offset=offset, bsz=bsz, device=device, dtype=x.dtype)

        if (not omni) or self.siglip_embedder is None:
            cap_feats_len = embeds[0].shape[1] + offset
            embeds += (None,)
            freqs_cis += (None,)
        else:
            cap_feats_len += offset
            if siglip_feats is not None:
                b, h, w, c = siglip_feats.shape
                siglip_feats = siglip_feats.permute(0, 3, 1, 2).reshape(b, h * w, c)
                siglip_feats = self.siglip_embedder(siglip_feats)
                siglip_pos_ids = torch.zeros((bsz, siglip_feats.shape[1], 3), dtype=torch.float32, device=device)
                siglip_pos_ids[:, :, 0] = cap_feats_len + 2
                siglip_pos_ids[:, :, 1] = (torch.linspace(0, h * 8 - 1, steps=h, dtype=torch.float32, device=device).floor()).view(-1, 1).repeat(1, w).flatten()
                siglip_pos_ids[:, :, 2] = (torch.linspace(0, w * 8 - 1, steps=w, dtype=torch.float32, device=device).floor()).view(1, -1).repeat(h, 1).flatten()
                if self.siglip_pad_token is not None:
                    siglip_feats, pad_extra = pad_zimage(siglip_feats, self.siglip_pad_token, self.pad_tokens_multiple)  # TODO: double check
                    siglip_pos_ids = torch.nn.functional.pad(siglip_pos_ids, (0, 0, 0, pad_extra))
            else:
                if self.siglip_pad_token is not None:
                    siglip_feats = self.siglip_pad_token.to(device=device, dtype=x.dtype, copy=True).unsqueeze(0).repeat(bsz, self.pad_tokens_multiple, 1)
                    siglip_pos_ids = torch.zeros((bsz, siglip_feats.shape[1], 3), dtype=torch.float32, device=device)

            if siglip_feats is None:
                embeds += (None,)
                freqs_cis += (None,)
            else:
                embeds += (siglip_feats,)
                freqs_cis += (self.rope_embedder(siglip_pos_ids).movedim(1, 2),)

        B, C, H, W = x.shape
        x = self.x_embedder(x.view(B, C, H // pH, pH, W // pW, pW).permute(0, 2, 4, 3, 5, 1).flatten(3).flatten(1, 2))
        x_pos_ids = pos_ids_x(cap_feats_len + 1, H // pH, W // pW, bsz, device, transformer_options=transformer_options)
        if self.pad_tokens_multiple is not None:
            x, pad_extra = pad_zimage(x, self.x_pad_token, self.pad_tokens_multiple)
            x_pos_ids = torch.nn.functional.pad(x_pos_ids, (0, 0, 0, pad_extra))

        embeds += (x,)
        freqs_cis += (self.rope_embedder(x_pos_ids).movedim(1, 2),)
        return embeds, freqs_cis, cap_feats_len + len(freqs_cis) - 1