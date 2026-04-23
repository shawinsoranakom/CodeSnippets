def forward(
        self,
        x,
        context=None,
        mask=None,
        context_mask=None,
        mems=None,
        seq_len=0,
        return_hiddens=False,
    ):
        assert not (
            self.cross_attend ^ exists(context)
        ), "context must be passed in if cross_attend is set to True"

        hiddens = []
        intermediates = []
        prev_attn = None
        prev_cross_attn = None
        rotary_pos_emb = None

        mems = mems.copy() if exists(mems) else [None] * self.num_attn_layers

        for ind, (layer_type, (norm, block, residual_fn)) in enumerate(
            zip(self.layer_types, self.layers)
        ):
            is_last = ind == (len(self.layers) - 1)

            if layer_type == "a":
                hiddens.append(x)
                layer_mem = mems.pop(0)

            residual = x

            if self.pre_norm:
                x = norm(x)

            if layer_type == "a":
                out, inter = block(
                    x,
                    mask=mask,
                    sinusoidal_emb=self.pia_pos_emb,
                    rel_pos=self.rel_pos,
                    rotary_pos_emb=rotary_pos_emb,
                    prev_attn=prev_attn,
                    mem=layer_mem,
                )
            elif layer_type == "c":
                out, inter = block(
                    x,
                    context=context,
                    mask=mask,
                    context_mask=context_mask,
                    prev_attn=prev_cross_attn,
                )
            elif layer_type == "f":
                out = block(x)

            x = residual_fn(out, residual)

            if layer_type in ("a", "c"):
                intermediates.append(inter)

            if layer_type == "a" and self.residual_attn:
                prev_attn = inter.pre_softmax_attn
            elif layer_type == "c" and self.cross_residual_attn:
                prev_cross_attn = inter.pre_softmax_attn

            if not self.pre_norm and not is_last:
                x = norm(x)

        if return_hiddens:
            intermediates = LayerIntermediates(
                hiddens=hiddens, attn_intermediates=intermediates
            )

            return x, intermediates

        return x