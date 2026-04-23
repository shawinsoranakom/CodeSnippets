def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        freqs_cis: Optional[torch.Tensor] = None,
        optimized_attention=None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        sliding_window: Optional[int] = None,
    ):
        batch_size, seq_length, _ = hidden_states.shape

        xq = self.q_proj(hidden_states)
        xk = self.k_proj(hidden_states)
        xv = self.v_proj(hidden_states)

        xq = xq.view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        xk = xk.view(batch_size, seq_length, self.num_kv_heads, self.head_dim).transpose(1, 2)
        xv = xv.view(batch_size, seq_length, self.num_kv_heads, self.head_dim).transpose(1, 2)

        if self.q_norm is not None:
            xq = self.q_norm(xq)
        if self.k_norm is not None:
            xk = self.k_norm(xk)

        xq, xk = apply_rope(xq, xk, freqs_cis=freqs_cis)

        present_key_value = None
        if past_key_value is not None:
            index = 0
            num_tokens = xk.shape[2]
            if len(past_key_value) > 0:
                past_key, past_value, index = past_key_value
                if past_key.shape[2] >= (index + num_tokens):
                    past_key[:, :, index:index + xk.shape[2]] = xk
                    past_value[:, :, index:index + xv.shape[2]] = xv
                    xk = past_key[:, :, :index + xk.shape[2]]
                    xv = past_value[:, :, :index + xv.shape[2]]
                    present_key_value = (past_key, past_value, index + num_tokens)
                else:
                    xk = torch.cat((past_key[:, :, :index], xk), dim=2)
                    xv = torch.cat((past_value[:, :, :index], xv), dim=2)
                    present_key_value = (xk, xv, index + num_tokens)
            else:
                present_key_value = (xk, xv, index + num_tokens)

            if sliding_window is not None and xk.shape[2] > sliding_window:
                xk = xk[:, :, -sliding_window:]
                xv = xv[:, :, -sliding_window:]
                attention_mask = attention_mask[..., -sliding_window:] if attention_mask is not None else None

        xk = xk.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)
        xv = xv.repeat_interleave(self.num_heads // self.num_kv_heads, dim=1)

        output = optimized_attention(xq, xk, xv, self.num_heads, mask=attention_mask, skip_reshape=True)
        return self.o_proj(output), present_key_value