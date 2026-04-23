def cuda_kernels_forward(
        self,
        hidden_states: torch.Tensor,
        cache_params: Cache | None = None,
        attention_mask: torch.LongTensor | None = None,
    ):
        batch_size, seq_len, _ = hidden_states.shape
        use_precomputed_states = (
            cache_params is not None and cache_params.has_previous_state(self.layer_idx) and seq_len == 1
        )
        # 1. Gated MLP's linear projection
        projected_states = self.in_proj(hidden_states).transpose(1, 2)

        # We can't use `mamba_inner_fn` even if in training and without cache params because we have the
        # inner layernorms which isn't supported by this fused kernel
        hidden_states, gate = projected_states.chunk(2, dim=1)

        if attention_mask is not None:
            hidden_states = hidden_states * attention_mask.unsqueeze(1)

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
            if cache_params is not None:
                conv_states = nn.functional.pad(hidden_states, (self.conv_kernel_size - hidden_states.shape[-1], 0))
                cache_params.update_conv_state(conv_states, self.layer_idx)
            hidden_states = causal_conv1d_fn(hidden_states, conv_weights, self.conv1d.bias, activation=self.activation)

        if attention_mask is not None:
            hidden_states = hidden_states * attention_mask.unsqueeze(1)

        # 3. State Space Model sequence transformation
        # 3.a. input varying initialization of time_step, B and C
        ssm_parameters = self.x_proj(hidden_states.transpose(1, 2))
        time_step, B, C = torch.split(
            ssm_parameters, [self.time_step_rank, self.ssm_state_size, self.ssm_state_size], dim=-1
        )

        time_step = self.dt_layernorm(time_step)
        B = self.b_layernorm(B)
        C = self.c_layernorm(C)

        # Here we need to apply dt_proj without the bias, as the bias is added in the selective scan kernel.
        # This is a hack to apply dt_proj while still using the forward pass of `torch.nn.Linear`, which is needed
        # in order to make quantization work. Quantization code replaces `torch.nn.Linear` layers with quantized
        # linear layers, and requires to call the forward pass directly.
        # Quantized model can't work with the original code:
        # ```discrete_time_step = self.dt_proj.weight @ time_step.transpose(1, 2)```
        time_proj_bias = self.dt_proj.bias.data
        with torch.no_grad():
            self.dt_proj.bias.data = torch.zeros_like(self.dt_proj.bias.data)
        discrete_time_step = self.dt_proj(time_step).transpose(1, 2)
        with torch.no_grad():
            self.dt_proj.bias.data = time_proj_bias

        A = -torch.exp(self.A_log.float())
        # 3.c perform the recurrence y ← SSM(A, B, C)(x)
        time_proj_bias = time_proj_bias.float() if time_proj_bias is not None else None
        if use_precomputed_states:
            scan_outputs = selective_state_update(
                cache_params.layers[self.layer_idx].recurrent_states,
                hidden_states[..., 0],
                discrete_time_step[..., 0],
                A,
                B[:, 0],
                C[:, 0],
                self.D,
                gate[..., 0],
                time_proj_bias,
                dt_softplus=True,
            ).unsqueeze(-1)
        else:
            scan_outputs, ssm_state = selective_scan_fn(
                hidden_states,
                discrete_time_step,
                A,
                B.transpose(1, 2),
                C.transpose(1, 2),
                self.D.float(),
                gate,
                time_proj_bias,
                delta_softplus=True,
                return_last_state=True,
            )
            if ssm_state is not None and cache_params is not None:
                cache_params.update_recurrent_state(ssm_state, self.layer_idx)

        # 4. Final linear projection
        contextualized_states = self.out_proj(scan_outputs.transpose(1, 2))

        return contextualized_states