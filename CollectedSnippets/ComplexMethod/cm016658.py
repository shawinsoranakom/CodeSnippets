def forward(
        self,
        x,
        context = None,
        global_cond=None,
        mask = None,
        context_mask = None,
        rotary_pos_emb = None,
        transformer_options={}
    ):
        if self.global_cond_dim is not None and self.global_cond_dim > 0 and global_cond is not None:

            scale_self, shift_self, gate_self, scale_ff, shift_ff, gate_ff = self.to_scale_shift_gate(global_cond).unsqueeze(1).chunk(6, dim = -1)

            # self-attention with adaLN
            residual = x
            x = self.pre_norm(x)
            x = x * (1 + scale_self) + shift_self
            x = self.self_attn(x, mask = mask, rotary_pos_emb = rotary_pos_emb, transformer_options=transformer_options)
            x = x * torch.sigmoid(1 - gate_self)
            x = x + residual

            if context is not None:
                x = x + self.cross_attn(self.cross_attend_norm(x), context = context, context_mask = context_mask, transformer_options=transformer_options)

            if self.conformer is not None:
                x = x + self.conformer(x)

            # feedforward with adaLN
            residual = x
            x = self.ff_norm(x)
            x = x * (1 + scale_ff) + shift_ff
            x = self.ff(x)
            x = x * torch.sigmoid(1 - gate_ff)
            x = x + residual

        else:
            x = x + self.self_attn(self.pre_norm(x), mask = mask, rotary_pos_emb = rotary_pos_emb, transformer_options=transformer_options)

            if context is not None:
                x = x + self.cross_attn(self.cross_attend_norm(x), context = context, context_mask = context_mask, transformer_options=transformer_options)

            if self.conformer is not None:
                x = x + self.conformer(x)

            x = x + self.ff(self.ff_norm(x))

        return x