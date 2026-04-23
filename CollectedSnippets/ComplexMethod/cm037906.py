def forward(
        self,
        x: torch.Tensor,
        tgt_sizes: torch.Tensor,
        # temporal_ids for high refresh rate videos
        temporal_ids=None,
    ) -> torch.Tensor:
        assert x.shape[0] == tgt_sizes.shape[0]
        bs = x.shape[0]

        device = x.device
        dtype = x.dtype

        patch_len = tgt_sizes[:, 0] * tgt_sizes[:, 1]

        self._adjust_pos_cache(tgt_sizes, device=device)

        temporal_pos_emb = False
        temporal_ids_flatten = None
        if temporal_ids is not None:
            # example: [[-1], [-1], [2, 6, 9]]
            temporal_ids_flatten = list(chain.from_iterable(temporal_ids))
            max_temporal_size = max(temporal_ids_flatten, default=0)
            if max_temporal_size > -1:
                temporal_pos_emb = True
            if max_temporal_size > self.max_temporal_size:
                self._adjust_temporal_pos_cache(max_temporal_size, device)

        max_patch_len = patch_len.max().item()
        assert isinstance(max_patch_len, int)

        key_padding_mask = torch.zeros(
            (bs, max_patch_len), dtype=torch.bool, device=device
        )

        x, _ = self.kv_proj(x)  # B * L * D
        x = self.ln_kv(x).permute(1, 0, 2)  # L * B * D
        q = self.ln_q(self.query)  # Q * D

        pos_embed_2d = []
        pos_embed_temporal = []
        for i in range(bs):
            tgt_h, tgt_w = tgt_sizes[i]
            if temporal_pos_emb:
                if temporal_ids_flatten[i] == -1:
                    pos_embed_temporal.append(
                        torch.zeros(self.embed_dim, dtype=dtype, device=device)
                    )
                else:
                    pos_embed_temporal.append(
                        self.temporal_pos_embed[temporal_ids_flatten[i]].to(dtype)
                    )  # D

            pos_embed_2d.append(
                self.pos_embed[:tgt_h, :tgt_w, :].reshape((tgt_h * tgt_w, -1)).to(dtype)
            )  # patches * D
            key_padding_mask[i, patch_len[i] :] = True

        pos_embed_2d = torch.nn.utils.rnn.pad_sequence(
            pos_embed_2d, batch_first=True, padding_value=0.0
        ).permute(1, 0, 2)  # BLD => L * B * D

        k = x + pos_embed_2d
        v = x
        if pos_embed_temporal:
            k += torch.stack(pos_embed_temporal, dim=0)
            bs = len(temporal_ids)
            merge_k = []
            merge_v = []
            merge_key_padding_mask = []

            start = 0
            for tp in temporal_ids:
                end = start + len(tp)
                # L * (end-start) * D -> (end-start) * L * D
                # -> 1 * L*(end-start) * D
                merge_k.append(
                    k[:, start:end, :].permute(1, 0, 2).reshape(-1, self.embed_dim)
                )
                merge_v.append(
                    v[:, start:end, :].permute(1, 0, 2).reshape(-1, self.embed_dim)
                )
                merge_key_padding_mask.append(
                    key_padding_mask[start:end, :].reshape(-1, 1)
                )

                start = end

            k = torch.nn.utils.rnn.pad_sequence(
                merge_k, batch_first=True, padding_value=0.0
            ).permute(1, 0, 2)  # L*(end-start)
            v = torch.nn.utils.rnn.pad_sequence(
                merge_v, batch_first=True, padding_value=0.0
            ).permute(1, 0, 2)  # L*(end-start)
            key_padding_mask = torch.nn.utils.rnn.pad_sequence(
                merge_key_padding_mask, batch_first=True, padding_value=True
            ).squeeze(-1)

        out = self.attn(
            self._repeat(q, bs),  # Q * B * D
            k,  # L * B * D +  L * B * D
            v,
            key_padding_mask=key_padding_mask,
        )[0]
        #  out: Q * B * D
        x = out.permute(1, 0, 2)  # B * Q * D

        x = self.ln_post(x)
        x = x @ self.proj
        return x