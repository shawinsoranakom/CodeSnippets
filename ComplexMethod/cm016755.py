def forward(self, x, past_key_value=None, **kwargs):
        batch_size, seq_len, _ = x.shape

        use_recurrent = (
            past_key_value is not None
            and past_key_value[2] > 0
            and seq_len == 1
        )

        # Projections (shared)
        mixed_qkv = self.in_proj_qkv(x).transpose(1, 2)  # [B, conv_dim, seq_len]
        z = self.in_proj_z(x)
        b = self.in_proj_b(x)
        a = self.in_proj_a(x)

        # Conv1d
        if use_recurrent:
            recurrent_state, conv_state, step_index = past_key_value
            conv_weight = comfy.model_management.cast_to_device(self.conv1d.weight, mixed_qkv.device, mixed_qkv.dtype).squeeze(1)
            conv_bias = comfy.model_management.cast_to_device(self.conv1d.bias, mixed_qkv.device, mixed_qkv.dtype) if self.conv1d.bias is not None else None
            mixed_qkv = torch_causal_conv1d_update(mixed_qkv, conv_state, conv_weight, conv_bias)
        else:
            if past_key_value is not None:
                recurrent_state, conv_state, step_index = past_key_value
                conv_state_init = F.pad(mixed_qkv, (self.conv_kernel_size - mixed_qkv.shape[-1], 0))
                conv_state.copy_(conv_state_init[:, :, -conv_state.shape[-1]:])
            mixed_qkv = F.silu(self.conv1d(mixed_qkv)[:, :, :seq_len])

        # Split QKV and compute beta/g
        mixed_qkv = mixed_qkv.transpose(1, 2)  # [B, seq_len, conv_dim]
        query, key, value = mixed_qkv.split([self.key_dim, self.key_dim, self.value_dim], dim=-1)
        beta = b.sigmoid()
        g = -self.A_log.float().exp() * F.softplus(a.float() + self.dt_bias.float())

        # Delta rule
        if use_recurrent:
            # single-token path: work in [B, heads, dim] without seq dim
            query = query.reshape(batch_size, self.num_key_heads, self.key_head_dim)
            key = key.reshape(batch_size, self.num_key_heads, self.key_head_dim)
            value = value.reshape(batch_size, self.num_value_heads, self.value_head_dim)

            if self.num_value_heads != self.num_key_heads:
                rep = self.num_value_heads // self.num_key_heads
                query = query.repeat_interleave(rep, dim=1)
                key = key.repeat_interleave(rep, dim=1)

            scale = self.key_head_dim ** -0.5
            q = F.normalize(query.float(), dim=-1) * scale
            k = F.normalize(key.float(), dim=-1)
            v = value.float()
            beta_t = beta.reshape(batch_size, -1)
            g_t = g.reshape(batch_size, -1).exp()

            # In-place state update: [B, heads, k_dim, v_dim]
            recurrent_state.mul_(g_t[:, :, None, None])
            kv_mem = torch.einsum('bhk,bhkv->bhv', k, recurrent_state)
            delta = (v - kv_mem) * beta_t[:, :, None]
            recurrent_state.add_(k.unsqueeze(-1) * delta.unsqueeze(-2))
            core_attn_out = torch.einsum('bhk,bhkv->bhv', q, recurrent_state)

            core_attn_out = core_attn_out.to(x.dtype).unsqueeze(1)
            present_key_value = (recurrent_state, conv_state, step_index + 1)
        else:
            query = query.reshape(batch_size, seq_len, -1, self.key_head_dim)
            key = key.reshape(batch_size, seq_len, -1, self.key_head_dim)
            value = value.reshape(batch_size, seq_len, -1, self.value_head_dim)

            if self.num_value_heads != self.num_key_heads:
                rep = self.num_value_heads // self.num_key_heads
                query = query.repeat_interleave(rep, dim=2)
                key = key.repeat_interleave(rep, dim=2)

            core_attn_out, last_recurrent_state = torch_chunk_gated_delta_rule(
                query, key, value, g=g, beta=beta,
                initial_state=None,
                output_final_state=past_key_value is not None,
            )

            present_key_value = None
            if past_key_value is not None:
                if last_recurrent_state is not None:
                    recurrent_state.copy_(last_recurrent_state.to(recurrent_state.dtype))
                present_key_value = (recurrent_state, conv_state, step_index + seq_len)

        # Gated norm + output projection (shared)
        core_attn_out = self.norm(core_attn_out.reshape(-1, self.value_head_dim), z.reshape(-1, self.value_head_dim))
        output = self.out_proj(core_attn_out.reshape(batch_size, seq_len, -1))
        return output, present_key_value