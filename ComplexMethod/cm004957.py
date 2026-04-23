def cuda_kernels_forward(
        self, hidden_states: torch.Tensor, cache_params: Cache | None = None, attention_mask=None
    ):
        batch_size, seq_len, _ = hidden_states.shape
        use_precomputed_states = cache_params is not None and cache_params.has_previous_state and seq_len == 1

        # 1. Gated linear projection
        projected_states = self.in_proj(hidden_states).transpose(1, 2)

        hidden_states, gate = projected_states.view(batch_size, -1, 2, seq_len).chunk(2, dim=2)
        hidden_states = hidden_states.squeeze(2).contiguous()
        gate = gate.squeeze(2)
        gate = gate.reshape(batch_size, self.n_mamba_heads, -1, seq_len).transpose(0, 1)

        # 2. Convolution sequence transformation
        conv_weights = self.conv1d.weight.view(self.conv1d.weight.size(0), self.conv1d.weight.size(2))
        if use_precomputed_states:
            hidden_states = causal_conv1d_update(
                hidden_states.squeeze(-1),
                cache_params.layers[self.layer_idx].conv_states,
                conv_weights,
                self.conv1d.bias,
                self.activation,
            )
            hidden_states = hidden_states.unsqueeze(-1)
        else:
            if attention_mask is not None and not torch.all(attention_mask == 1):
                hidden_states = hidden_states * attention_mask.unsqueeze(1)
            if cache_params is not None:
                conv_states = nn.functional.pad(hidden_states, (self.conv_kernel_size - hidden_states.shape[-1], 0))
                conv_states = cache_params.update_conv_state(conv_states, self.layer_idx)
            hidden_states = causal_conv1d_fn(hidden_states, conv_weights, self.conv1d.bias, activation=self.activation)
            if attention_mask is not None and not torch.all(attention_mask == 1):
                hidden_states = hidden_states * attention_mask.unsqueeze(1)

        # 3. SSM sequence transformation
        # 3.a. input varying initialization of time_step, B and C

        hidden_states = hidden_states.reshape(-1, self.n_mamba_heads, self.mamba_head_dim, seq_len).transpose(0, 1)
        ssm_parameters = (self.x_proj_weight[:, None, :, :] @ hidden_states).transpose(-1, -2)

        time_step, B, C = torch.split(
            ssm_parameters, [self.time_step_rank, self.ssm_state_size, self.ssm_state_size], dim=-1
        )

        discrete_time_step = self.dt_proj_weight[:, None] @ time_step.transpose(-1, -2)

        A = -torch.exp(self.A_log.float())

        # 3.c perform the recurrence y ← SSM(A, B, C)(x)
        time_proj_bias = self.dt_proj_bias.float() if self.dt_proj_bias is not None else None
        scan_outputs = torch.empty((batch_size, 0, seq_len), device=hidden_states.device, dtype=hidden_states.dtype)

        if use_precomputed_states:
            for n in range(self.n_mamba_heads):
                scan_outputs_ = selective_state_update(
                    cache_params.layers[self.layer_idx].recurrent_states[:, n],
                    hidden_states[n, ..., 0],
                    discrete_time_step[n, ..., 0],
                    A[n],
                    B[n, :, 0],
                    C[n, :, 0],
                    self.D[n],
                    gate[n, ..., 0],
                    time_proj_bias[n],
                    dt_softplus=True,
                ).unsqueeze(-1)
                scan_outputs = torch.cat((scan_outputs, scan_outputs_), dim=1)

        else:
            ssm_state = torch.empty(
                (batch_size, 0, self.mamba_head_dim, self.ssm_state_size),
                device=hidden_states.device,
                dtype=hidden_states.dtype,
            )
            for n in range(self.n_mamba_heads):
                scan_outputs_, ssm_state_ = selective_scan_fn(
                    hidden_states[n],
                    discrete_time_step[n],
                    A[n],
                    B[n].transpose(1, 2),
                    C[n].transpose(1, 2),
                    self.D[n].float(),
                    gate[n],
                    time_proj_bias[n],
                    delta_softplus=True,
                    return_last_state=True,
                )
                scan_outputs = torch.cat((scan_outputs, scan_outputs_), dim=1).contiguous()
                ssm_state = torch.cat((ssm_state, ssm_state_.unsqueeze(1)), dim=1)
            if ssm_state is not None and cache_params is not None:
                cache_params.update_recurrent_state(ssm_state, self.layer_idx)

        # 4. Final linear projection
        contextualized_states = self.out_proj(scan_outputs.transpose(1, 2))
        return contextualized_states