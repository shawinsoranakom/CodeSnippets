def torch_forward(self, input_states, cache_params: Cache | None=None, attention_mask: torch.Tensor | None = None):
        batch_size, seq_len, _ = input_states.shape
        dtype = input_states.dtype
        # Gated MLP's linear projection
        if cache_params is not None and cache_params.has_previous_state(self.layer_idx):
            projected_states = self.in_proj(input_states)
        else:
            if attention_mask is not None:
                # tune out hidden states for pad tokens, see https://github.com/state-spaces/mamba/issues/66
                input_states = (input_states * attention_mask[:, :, None]).to(dtype)
            projected_states = self.in_proj(input_states)
        d_mlp = (projected_states.shape[-1] - 2 * self.intermediate_size - 2 * self.n_groups * self.ssm_state_size- self.num_heads) // 2
        _, _, gate, hidden_states, dt = projected_states.split(
                [d_mlp, d_mlp, self.intermediate_size,  self.conv_dim, self.num_heads], dim=-1
        )
        hidden_states = hidden_states.transpose(1, 2)

        use_precomputed_state = cache_params is not None and cache_params.has_previous_state(self.layer_idx)

        # Convolution sequence transformation
        if use_precomputed_state:
            conv_state = cache_params.update_conv_state(hidden_states, self.layer_idx)
            hidden_states = torch.sum(conv_state * self.conv1d.weight[:, 0, :], dim=-1)
            if self.use_conv_bias:
                hidden_states += self.conv1d.bias
            hidden_states = self.act(hidden_states).to(dtype)[:, None, ...]         # [batch, 1, intermediate_size] : decoding
        else:
            if cache_params is not None:
                conv_state = nn.functional.pad(
                    hidden_states,
                    (self.conv_kernel_size - hidden_states.shape[-1], 0)
                )
                conv_state = cache_params.update_conv_state(conv_state, self.layer_idx)

            hidden_states = self.act(self.conv1d(hidden_states)[..., :seq_len].transpose(1, 2))
            if attention_mask is not None:
                dtype = hidden_states.dtype
                # tune out hidden states for pad tokens, see https://github.com/state-spaces/mamba/issues/66
                hidden_states = (hidden_states * attention_mask[:, :, None]).to(dtype)

        hidden_states, B, C = torch.split(hidden_states, [self.intermediate_size, self.n_groups * self.ssm_state_size, self.n_groups * self.ssm_state_size], dim=-1)
        A = -torch.exp(self.A_log.float())                            # [num_heads]
        if use_precomputed_state:
            # Note: there is no need to pad parameter matrices here, as there is just one new token
            # for batched generation
            dt = dt[:, None, ...] if dt.ndim == 2 else dt[:, 0, :][:, None, ...]
            dt = dt.transpose(1, 2).expand(batch_size, dt.shape[-1], self.head_dim)
            # [num_heads] -> [num_heads, head_dim]
            dt_bias = self.dt_bias[..., None].expand(self.dt_bias.shape[0], self.head_dim)

            dt = torch.nn.functional.softplus(dt + dt_bias.to(dt.dtype))
            dt = torch.clamp(dt, self.time_step_min) #, self.time_step_max)
            A = A[..., None, None].expand(self.num_heads, self.head_dim, self.ssm_state_size).to(dtype=torch.float32)
            # [bsz, num_heads, head_dim, state_size]
            dA = torch.exp(dt[..., None] * A)

            # Discretize B
            # [bsz, n_groups * state_size] -> [bsz, n_groups, 1, state_size] ->
            # -> [bsz, n_groups, group to head repetition factor, state_size] -> [bsz, num_heads, state_size]
            B = B.reshape(batch_size, self.n_groups, -1)[..., None, :]
            B = B.expand(batch_size, self.n_groups, self.num_heads // self.n_groups, B.shape[-1]).contiguous()
            B = B.reshape(batch_size, -1, B.shape[-1])
            # [bsz, num_heads, head_dim, state_size]
            dB = dt[..., None] * B[..., None, :]

            # Discretize x into dB
            # [bsz, intermediate_size] -> [bsz, num_heads, head_dim]
            hidden_states = hidden_states.reshape(batch_size, -1, self.head_dim)
            dBx = dB * hidden_states[..., None]

            # State calculation
            ssm_states = cache_params.layers[self.layer_idx].recurrent_states.clone()
            ssm_states = ssm_states * dA + dBx
            ssm_states = cache_params.update_recurrent_state(ssm_states, self.layer_idx)

            # Subsequent output
            # [bsz, n_groups * state_size] -> [bsz, num_heads, state_size]
            C = C.reshape(batch_size, self.n_groups, -1)[..., None, :]
            C = C.expand(batch_size, self.n_groups, self.num_heads // self.n_groups, C.shape[-1]).contiguous()
            C = C.reshape(batch_size, -1, C.shape[-1])
            # [bsz, num_heads, head_dim]

            ssm_states = ssm_states.to(C.dtype)  # Shape: [b, h, d, n]
            # Reshape ssm_states to merge the first two dimensions
            ssm_states_reshaped = ssm_states.view(batch_size * self.num_heads, self.head_dim, self.ssm_state_size)  # Shape: [b*h, d, n]
            C_reshaped = C.view(batch_size * self.num_heads, self.ssm_state_size, 1)  # Shape: [b*h, n, 1]
            y = torch.bmm(ssm_states_reshaped, C_reshaped)
            y = y.view(batch_size, self.num_heads, self.head_dim)

            # D skip connection
            # [num_heads] -> [num_heads, head_dim]
            D = self.D[..., None].expand(self.D.shape[0], self.head_dim)
            y = (y + hidden_states * D).to(y.dtype)

            # [bsz, num_heads, head_dim] -> [bsz, 1, intermediate_size]
            y = y.reshape(batch_size, -1)[:, None, ...]
        else:
            # begin ssd naive implementation without einsums
            dt = nn.functional.softplus(dt + self.dt_bias)
            dt = torch.clamp(dt, self.time_step_min)
            hidden_states = hidden_states.reshape(batch_size, seq_len, -1, self.head_dim).float()
            B = B.reshape(batch_size, seq_len,  -1, self.ssm_state_size).float()
            C = C.reshape(batch_size, seq_len, -1, self.ssm_state_size).float()
            B = B.repeat_interleave(self.num_heads // self.n_groups, dim=2, output_size=self.num_heads)
            C = C.repeat_interleave(self.num_heads // self.n_groups, dim=2, output_size=self.num_heads)
            pad_size = (self.chunk_size - seq_len % self.chunk_size) % self.chunk_size

            D_residual = self.D[..., None] * pad_tensor_by_size(hidden_states, pad_size)

            # Discretize x and A
            hidden_states = hidden_states * dt[..., None]
            A = A.to(hidden_states.dtype) * dt

            # Rearrange into blocks/chunks
            hidden_states, A, B, C = [reshape_into_chunks(t, pad_size, self.chunk_size) for t in (hidden_states, A, B, C)]


            # [bsz, -1, chunk_size, num_heads] -> [bsz, num_heads, -1, chunk_size]
            A = A.permute(0, 3, 1, 2)
            A_cumsum = torch.cumsum(A, dim=-1)

            # 1. Compute the output for each intra-chunk (diagonal blocks)
            # This is the analog of a causal mask
            L = torch.exp(segment_sum(A))

            # First, contraction of C and B to get G (attention-weights like)
            G_intermediate = C[:, :, :, None, :, :] * B[:, :, None, :, : ,:]  # shape: (b, c, l, s, h, n)
            G = G_intermediate.sum(dim=-1)  # shape: (b, c, l, s, h)


            # Step 2: Compute M, equivalent to applying attention mask to weights
            M_intermediate = G[..., None] * L.permute(0, 2, 3, 4, 1)[..., None]
            M = M_intermediate.sum(dim=-1)

            # Step 3: Compute Y_diag (apply to values)
            Y_diag = (M[..., None] * hidden_states[:, :, None]).sum(3)

            # (right term of low-rank factorization of off-diagonal blocks; B terms)

            decay_states = torch.exp(A_cumsum[:, :, :, -1:] - A_cumsum)
            B_decay_contraction = B * decay_states.permute(0, 2, 3, 1)[..., None]
            # permute back B * decay states
            states = (B_decay_contraction.permute(0, 1, 3, 2, 4)[..., None]  * hidden_states.permute(0, 1, 3, 2, 4)[..., None, :]).sum(dim=3).permute(0, 1, 2, 4, 3)
            previous_states = torch.zeros_like(states[:, :1])
            states = torch.cat([previous_states, states], dim=1)
            decay_chunk = torch.exp(segment_sum(nn.functional.pad(A_cumsum[:, :, :, -1], (1, 0))))

            states_permuted = states.permute(0, 2, 1, 3, 4)
            result = (decay_chunk[..., None, None] * states_permuted[:, :, None, ...]).sum(dim=2)
            new_states = result.permute(0, 2, 1, 3, 4)
            states, ssm_state = new_states[:, :-1], new_states[:, -1]

            # Compute state -> output conversion per chunk
            # (left term of low-rank factorization of off-diagonal blocks; C terms)
            state_decay_out = torch.exp(A_cumsum)
            # compute Yoff
            C_times_states = (C[..., None, :] * states[:, :, None, ...])
            state_decay_out_permuted = state_decay_out.permute(0, 2, 3, 1)
            Y_off = (C_times_states.sum(-1) * state_decay_out_permuted[..., None])
            # Add output of intra-chunk and inter-chunk terms (diagonal and off-diagonal blocks)

            y = Y_diag + Y_off
            # [bsz, -1, self.chunk_size, num_heads, head_dim] -> [bsz, (padded) seq_len, num_heads, head_dim]
            y = y.reshape(batch_size, -1, self.num_heads, self.head_dim)

            y = y + D_residual
            # Cutting off padded chunks
            if pad_size > 0:
                y = y[:, :seq_len, :, :]
            y = y.reshape(batch_size, seq_len, -1)
            if ssm_state is not None and cache_params is not None:
                cache_params.update_recurrent_state(ssm_state, self.layer_idx)

        scan_output = self.norm(y, gate)

        # end ssd naive

        # 4. Final linear projection
        contextualized_states = self.out_proj(scan_output.to(dtype))  # [batch, seq_len, hidden_size]
        return contextualized_states