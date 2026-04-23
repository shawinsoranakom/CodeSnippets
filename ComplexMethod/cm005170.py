def forward(
        self,
        h,
        g,
        attn_mask_h,
        attn_mask_g,
        r,
        seg_mat,
        mems=None,
        target_mapping=None,
        output_attentions=False,
    ):
        if g is not None:
            # Two-stream attention with relative positional encoding.
            # content based attention score
            if mems is not None and mems.dim() > 1:
                cat = torch.cat([mems, h], dim=0)
            else:
                cat = h

            # content-based key head
            k_head_h = torch.einsum("ibh,hnd->ibnd", cat, self.k)

            # content-based value head
            v_head_h = torch.einsum("ibh,hnd->ibnd", cat, self.v)

            # position-based key head
            k_head_r = torch.einsum("ibh,hnd->ibnd", r, self.r)

            # h-stream
            # content-stream query head
            q_head_h = torch.einsum("ibh,hnd->ibnd", h, self.q)

            # core attention ops
            attn_vec_h = self.rel_attn_core(
                q_head_h,
                k_head_h,
                v_head_h,
                k_head_r,
                seg_mat=seg_mat,
                attn_mask=attn_mask_h,
                output_attentions=output_attentions,
            )

            if output_attentions:
                attn_vec_h, attn_prob_h = attn_vec_h

            # post processing
            output_h = self.post_attention(h, attn_vec_h)

            # g-stream
            # query-stream query head
            q_head_g = torch.einsum("ibh,hnd->ibnd", g, self.q)

            # core attention ops
            if target_mapping is not None:
                q_head_g = torch.einsum("mbnd,mlb->lbnd", q_head_g, target_mapping)
                attn_vec_g = self.rel_attn_core(
                    q_head_g,
                    k_head_h,
                    v_head_h,
                    k_head_r,
                    seg_mat=seg_mat,
                    attn_mask=attn_mask_g,
                    output_attentions=output_attentions,
                )

                if output_attentions:
                    attn_vec_g, attn_prob_g = attn_vec_g

                attn_vec_g = torch.einsum("lbnd,mlb->mbnd", attn_vec_g, target_mapping)
            else:
                attn_vec_g = self.rel_attn_core(
                    q_head_g,
                    k_head_h,
                    v_head_h,
                    k_head_r,
                    seg_mat=seg_mat,
                    attn_mask=attn_mask_g,
                    output_attentions=output_attentions,
                )

                if output_attentions:
                    attn_vec_g, attn_prob_g = attn_vec_g

            # post processing
            output_g = self.post_attention(g, attn_vec_g)

            if output_attentions:
                attn_prob = attn_prob_h, attn_prob_g

        else:
            # Multi-head attention with relative positional encoding
            if mems is not None and mems.dim() > 1:
                cat = torch.cat([mems, h], dim=0)
            else:
                cat = h

            # content heads
            q_head_h = torch.einsum("ibh,hnd->ibnd", h, self.q)
            k_head_h = torch.einsum("ibh,hnd->ibnd", cat, self.k)
            v_head_h = torch.einsum("ibh,hnd->ibnd", cat, self.v)

            # positional heads
            # type casting for fp16 support
            k_head_r = torch.einsum("ibh,hnd->ibnd", r.type(self.r.dtype), self.r)

            # core attention ops
            attn_vec = self.rel_attn_core(
                q_head_h,
                k_head_h,
                v_head_h,
                k_head_r,
                seg_mat=seg_mat,
                attn_mask=attn_mask_h,
                output_attentions=output_attentions,
            )

            if output_attentions:
                attn_vec, attn_prob = attn_vec

            # post processing
            output_h = self.post_attention(h, attn_vec)
            output_g = None

        outputs = (output_h, output_g)
        if output_attentions:
            outputs = outputs + (attn_prob,)
        return outputs