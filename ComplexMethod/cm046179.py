def _apply_self_attention(self, tgt, tgt_query_pos, dac, dac_use_selfatt_ln, presence_token, self_attn_mask):
        """Apply self-attention with optional DAC splitting."""
        if self.self_attn is None:
            return tgt

        if dac:
            # Split queries for DAC (detect-and-classify)
            assert tgt.shape[0] % 2 == 0, "DAC requires even number of queries"
            num_o2o_queries = tgt.shape[0] // 2
            tgt_o2o = tgt[:num_o2o_queries]
            tgt_query_pos_o2o = tgt_query_pos[:num_o2o_queries]
            tgt_o2m = tgt[num_o2o_queries:]
        else:
            tgt_o2o = tgt
            tgt_query_pos_o2o = tgt_query_pos

        # Handle presence token
        if presence_token is not None:
            tgt_o2o = torch.cat([presence_token, tgt_o2o], dim=0)
            tgt_query_pos_o2o = torch.cat([torch.zeros_like(presence_token), tgt_query_pos_o2o], dim=0).to(
                tgt_o2o.dtype
            )
            tgt_query_pos = torch.cat([torch.zeros_like(presence_token), tgt_query_pos], dim=0)

        # Self-attention
        q = k = self.with_pos_embed(tgt_o2o, tgt_query_pos_o2o)
        tgt2 = self.self_attn(q, k, tgt_o2o, attn_mask=self_attn_mask)[0].to(tgt.dtype)
        tgt_o2o = tgt_o2o + self.dropout2(tgt2)

        # Recombine and normalize
        if dac:
            if not dac_use_selfatt_ln:
                tgt_o2o = self.norm2(tgt_o2o)
            tgt = torch.cat((tgt_o2o, tgt_o2m), dim=0)
            if dac_use_selfatt_ln:
                tgt = self.norm2(tgt)
        else:
            tgt = tgt_o2o
            tgt = self.norm2(tgt)

        return tgt, tgt_query_pos