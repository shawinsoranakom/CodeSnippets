def forward(
        self,
        x,
        context=None,
        mask=None,
        context_mask=None,
        rel_pos=None,
        sinusoidal_emb=None,
        rotary_pos_emb=None,
        prev_attn=None,
        mem=None,
        seq_len=0,
    ):
        if not self.training:
            self.is_export = True
        b, n, _, h, talking_heads, collab_heads, has_context = (
            *x.shape,
            self.heads,
            self.talking_heads,
            self.collab_heads,
            exists(context),
        )
        kv_input = default(context, x)

        q_input = x
        k_input = kv_input
        v_input = kv_input

        if exists(mem):
            k_input = paddle.concat((mem, k_input), axis=-2)
            v_input = paddle.concat((mem, v_input), axis=-2)

        if exists(sinusoidal_emb):
            # in shortformer, the query would start at a position offset depending on the past cached memory
            offset = k_input.shape[-2] - q_input.shape[-2]
            q_input = q_input + sinusoidal_emb(q_input, offset=offset)
            k_input = k_input + sinusoidal_emb(k_input)
        q = self.to_q(q_input)
        k = self.to_k(k_input)
        v = self.to_v(v_input)

        def rearrange_q_k_v(x, h, is_export):
            if is_export:
                b, n, h_d = paddle.shape(x)
            else:
                b, n, h_d = x.shape
            d = h_d // h
            return x.reshape([b, n, h, d]).transpose([0, 2, 1, 3])

        q, k, v = map(
            lambda t: rearrange_q_k_v(t, h, is_export=self.is_export), (q, k, v)
        )

        input_mask = None
        if any(map(exists, (mask, context_mask))):
            q_mask = default(
                mask,
                lambda: paddle.ones(
                    (b, n),
                ).cast(paddle.bool),
            )
            k_mask = q_mask if not exists(context) else context_mask
            k_mask = default(
                k_mask, lambda: paddle.ones((b, k.shape[-2])).cast(paddle.bool)
            )

            q_mask = q_mask.reshape([q_mask.shape[0], 1, q_mask.shape[1], 1])
            k_mask = k_mask.reshape([k_mask.shape[0], 1, 1, k_mask.shape[1]])
            input_mask = q_mask * k_mask

        if collab_heads:
            k = k.expand(-1, h, -1, -1)
        dots = einsum("b h i d, b h j d -> b h i j", q, k) * self.scale

        mask_value = max_neg_value(dots)

        if exists(prev_attn):
            dots = dots + prev_attn

        pre_softmax_attn = dots.clone()

        if talking_heads:
            dots = einsum(
                "b h i j, h k -> b k i j", dots, self.pre_softmax_proj
            ).contiguous()

        if exists(rel_pos):
            dots = rel_pos(dots)

        input_mask = input_mask.cast(paddle.bool)
        if exists(input_mask):

            dots.masked_fill_(~input_mask, mask_value)
            del input_mask

        if self.causal:
            i, j = dots.shape[-2:]
            r = paddle.arange(i)
            r_shape = r.shape[0]
            mask = r.reshape([1, 1, r_shape, 1]) < r.reshape([1, 1, 1, r_shape])

            if self.is_export:
                pad_list = [
                    paddle.to_tensor(0, dtype="int32"),
                    paddle.to_tensor(0, dtype="int32"),
                    paddle.to_tensor(j - i, dtype="int32"),
                    paddle.to_tensor(0, dtype="int32"),
                ]
                mask = F.pad(
                    mask.cast(paddle.int32),
                    paddle.to_tensor(pad_list).cast(paddle.int32),
                    value=False,
                ).cast(paddle.bool)
                dots = dots.masked_fill_(mask, mask_value)
            else:
                mask = F.pad(mask.cast(paddle.int32), (0, 0, j - i, 0), value=False)
                dots.masked_fill_(mask, mask_value)
            del mask
        if exists(self.sparse_topk) and self.sparse_topk < dots.shape[-1]:
            top, _ = dots.topk(self.sparse_topk, dim=-1)
            vk = top[..., -1].unsqueeze(-1).expand_as(dots)
            mask = dots < vk
            dots.masked_fill_(mask, mask_value)
            del mask

        attn = self.attn_fn(dots, axis=-1)
        post_softmax_attn = attn.clone()

        attn = self.dropout(attn)

        if talking_heads:
            attn = einsum(
                "b h i j, h k -> b k i j", attn, self.post_softmax_proj
            ).contiguous()
        out = einsum("b h i j, b h j d -> b h i d", attn, v)

        b, h, n, d = out.shape
        out = out.transpose([0, 2, 1, 3]).reshape([b, n, h * d])

        if exists(self.to_v_gate):
            gates = self.gate_v(x)
            out = out * gates.sigmoid()

        intermediates = Intermediates(
            pre_softmax_attn=pre_softmax_attn, post_softmax_attn=post_softmax_attn
        )

        return self.to_out(out), intermediates