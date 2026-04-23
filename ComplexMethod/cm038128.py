def forward(
        self,
        query: Tensor,
        key: Tensor,
        value: Tensor,
        pos_k: Tensor | None,
        pos_v: Tensor | None,
        mask: Tensor | None,
        relative_attention_bias: Tensor | None = None,
    ) -> Tensor:
        """Compute 'Scaled Dot Product Attention'.

        Args:
            query: query tensor (batch, time1, size)
            key: key tensor (batch, time2, size)
            value: value tensor (batch, time1, size)
            pos_k: key tensor used for relative positional embedding.
            pos_v: value tensor used for relative positional embedding.
            mask: mask tensor (batch, time1, time2)
            relative_attention_bias: bias added to attention logits w.r.t.
                relative positions
                (1, n_head, time1, time2)
        """
        n_batch = query.size(0)

        q = self.linear_q(query).view(n_batch, -1, self.h, self.d_k)  # (b, t, d)
        k = self.linear_k(key).view(n_batch, -1, self.h_k, self.d_k)  # (b, t, d)
        v = self.linear_v(value).view(n_batch, -1, self.h_k, self.d_k)
        q = (
            q.transpose(1, 2)
            if self.use_pt_scaled_dot_product_attention and not torch.jit.is_scripting()
            else q.transpose(1, 2) * self.inv_sqrt_d_k
        )
        k = k.transpose(1, 2)  # (batch, head_k, time2, d_k)
        v = v.transpose(1, 2)  # (batch, head_k, time2, d_k)

        if self.use_pt_scaled_dot_product_attention and not torch.jit.is_scripting():
            attn_mask = None
            if mask is not None:
                mask = mask.unsqueeze(1)
                if relative_attention_bias is not None:
                    attn_mask = mask + relative_attention_bias
                else:
                    attn_mask = mask
                if mask.dtype != q.dtype:
                    attn_mask = attn_mask.to(q.dtype)

            with torch.nn.attention.sdpa_kernel(
                [
                    torch.nn.attention.SDPBackend.FLASH_ATTENTION,
                    torch.nn.attention.SDPBackend.EFFICIENT_ATTENTION,
                    torch.nn.attention.SDPBackend.MATH,
                    torch.nn.attention.SDPBackend.CUDNN_ATTENTION,
                ]
            ):
                x = torch.nn.functional.scaled_dot_product_attention(
                    q,
                    k,
                    v,
                    attn_mask=attn_mask,
                    dropout_p=self.dropout_rate,
                )
        else:
            if self.h != self.h_k:
                q = q.reshape(n_batch, self.g, self.h_k, -1, self.d_k)
                A = torch.einsum("b g h t d, b h s d -> b h t s", q, k)
            else:
                A = torch.matmul(q, k.transpose(-2, -1))
            if pos_k is not None:
                if self.h != self.h_k:
                    B = torch.einsum("b g h t d, t s d -> b h t s", q, pos_k)
                else:
                    reshape_q = (
                        q.contiguous()
                        .view(n_batch * self.h, -1, self.d_k)
                        .transpose(0, 1)
                    )  # (t1,nh,dk)
                    B = torch.matmul(
                        reshape_q, pos_k.transpose(-2, -1)
                    )  # pos_k: (t1,dk,t2)
                    B = B.transpose(0, 1).view(
                        n_batch, self.h, pos_k.size(0), pos_k.size(1)
                    )
                scores = A + B
            else:
                scores = A

            if relative_attention_bias is not None:
                scores = scores + relative_attention_bias

            attn = masked_softmax(scores, mask)  # (batch, head, time1, time2)

            self.attn = attn

            p_attn = self.dropout(attn)
            x = torch.matmul(p_attn.to(v.dtype), v)  # (batch, head, time1, d_k)
            if pos_v is not None:
                reshape_attn = (
                    p_attn.contiguous()
                    .view(n_batch * self.h, pos_v.size(0), pos_v.size(1))
                    .transpose(0, 1)
                )  # (t1, bh, t2)

                attn_v = (
                    torch.matmul(reshape_attn, pos_v)
                    .transpose(0, 1)
                    .contiguous()
                    .view(n_batch, self.h, pos_v.size(0), self.d_k)
                )
                x = x + attn_v
        x = (
            x.transpose(1, 2).contiguous().view(n_batch, -1, self.h_k * self.d_k)
        )  # (batch, time1, d_model)

        return self.linear_out(x)