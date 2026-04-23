def forward_impl(self, hidden_states: torch.Tensor, output: torch.Tensor):
        """
        Run the Mamba-1 SSM pipeline.

        Steps
        -----
        1. Apply the gated-MLP linear projection to the raw input.
        2. Pass the projected sequence through the convolutional mixing layer.
        3. Feed the result into the State-Space Model (SSM) blocks.
        4. Perform the recurrence y ← SSM(A, B, C, Δ)(x)
           to produce contextual representations.
        5. Project the contextualised sequence back
           to the output embedding dimension.

        Batch handling
        --------------
        Prefill and decode tokens are processed by dedicated CUDA
        kernels for both the convolutional (conv1d) and SSM stages.
        In the case of a mixed batch (containing both prefill and
        decode tokens), both sets of kernels are executed independently
        and their outputs are concatenated before the final output projection.
        """

        forward_context: ForwardContext = get_forward_context()
        attn_metadata_raw = forward_context.attn_metadata

        assert self.cache_config is not None
        mamba_block_size = self.cache_config.mamba_block_size
        is_mamba_cache_all = self.cache_config.mamba_cache_mode == "all"

        attn_metadata: AttentionMetadata | None = None
        if attn_metadata_raw is not None:
            assert isinstance(attn_metadata_raw, dict)
            attn_metadata = attn_metadata_raw[self.prefix]
            assert isinstance(attn_metadata, Mamba1AttentionMetadata)
            query_start_loc_p = attn_metadata.query_start_loc_p
            state_indices_tensor_p = attn_metadata.state_indices_tensor_p
            state_indices_tensor_d = attn_metadata.state_indices_tensor_d
            conv_state = (
                self.kv_cache[0]
                if is_conv_state_dim_first()
                else self.kv_cache[0].transpose(-1, -2)
            )
            ssm_state = self.kv_cache[1]
            has_initial_states_p = attn_metadata.has_initial_states_p
            cu_chunk_seqlen_p = attn_metadata.cu_chunk_seqlen_p
            last_chunk_indices_p = attn_metadata.last_chunk_indices_p

        # 1. Gated MLP's linear projection
        projected_states = self.in_proj(hidden_states)[0].transpose(-2, -1)
        hidden_states_BC, gate = projected_states.chunk(2, dim=-2)

        conv_weights = self.conv1d.weight.view(
            self.conv1d.weight.size(0), self.conv1d.weight.size(2)
        )

        if attn_metadata is None:
            # V1 profile run
            hidden_states_BC = hidden_states_BC.contiguous()
            return self.out_proj(hidden_states_BC.transpose(-2, -1))[0]

        num_prefill_tokens = attn_metadata.num_prefill_tokens  # token count
        num_decode_tokens = attn_metadata.num_decode_tokens
        num_prefills = attn_metadata.num_prefills  # request count
        num_decodes = attn_metadata.num_decode_tokens  # token count (=request)
        has_prefill = num_prefill_tokens > 0
        has_decode = num_decode_tokens > 0
        num_actual_tokens = num_prefill_tokens + num_decode_tokens

        prefill_decode_split = split_batch_to_prefill_and_decode(
            hidden_states_BC,
            gate,
            num_prefill_tokens,
            num_decode_tokens,
        )
        hidden_states_BC_p = prefill_decode_split.hidden_states_BC_p
        hidden_states_BC_d = prefill_decode_split.hidden_states_BC_d
        gate_p = prefill_decode_split.gate_p
        gate_d = prefill_decode_split.gate_d

        if is_mamba_cache_all:
            block_idx_last_computed_token_d, block_idx_last_computed_token_p = (
                torch.split(
                    attn_metadata.block_idx_last_computed_token,
                    [num_decodes, num_prefills],
                    dim=0,
                )
            )
            block_idx_last_scheduled_token_d, block_idx_last_scheduled_token_p = (
                torch.split(
                    attn_metadata.block_idx_last_scheduled_token,
                    [num_decodes, num_prefills],
                    dim=0,
                )
            )

            block_idx_first_scheduled_token_p = (
                attn_metadata.block_idx_first_scheduled_token_p
            )
            num_computed_tokens_p = attn_metadata.num_computed_tokens_p
        else:
            block_idx_last_computed_token_d = None
            block_idx_last_computed_token_p = None
            block_idx_last_scheduled_token_d = None
            block_idx_last_scheduled_token_p = None
            block_idx_first_scheduled_token_p = None
            num_computed_tokens_p = None

        ssm_outputs = []

        if has_prefill:
            # 2. Convolution sequence transformation
            conv_out_p = causal_conv1d_fn(
                hidden_states_BC_p,
                conv_weights,
                self.conv1d.bias,
                activation=self.activation,
                conv_states=conv_state,
                has_initial_state=has_initial_states_p,
                cache_indices=state_indices_tensor_p,
                query_start_loc=query_start_loc_p,
                block_idx_first_scheduled_token=block_idx_first_scheduled_token_p,
                block_idx_last_scheduled_token=block_idx_last_scheduled_token_p,
                initial_state_idx=block_idx_last_computed_token_p,
                num_computed_tokens=num_computed_tokens_p,
                block_size_to_align=mamba_block_size,
            )
            # 3. State Space Model sequence transformations.
            discrete_time_step_p, B_p, C_p = self._ssm_transform(
                conv_out_p.transpose(-2, -1)
            )
            time_proj_bias = self._time_proj_bias()

            # 4. Perform the recurrence y ← SSM(A, B, C, Δ)(x)
            scan_out_p = selective_scan_fn(
                conv_out_p,
                ssm_state,
                discrete_time_step_p,
                self.A,
                B_p.transpose(-2, -1),
                C_p.transpose(-2, -1),
                self.D.float(),
                gate_p,
                time_proj_bias,
                delta_softplus=True,
                cache_indices=state_indices_tensor_p,
                has_initial_state=has_initial_states_p,
                query_start_loc=query_start_loc_p,
                block_size=mamba_block_size,
                block_idx_first_scheduled_token=block_idx_first_scheduled_token_p,
                block_idx_last_scheduled_token=block_idx_last_scheduled_token_p,
                initial_state_idx=block_idx_last_computed_token_p,
                cu_chunk_seqlen=cu_chunk_seqlen_p,
                last_chunk_indices=last_chunk_indices_p,
            )
            ssm_outputs.append(scan_out_p)

        if has_decode:
            # state_indices_tensor_d is assigned when attn_metadata is not None,
            # and has_decode is only True when attn_metadata is not None
            assert state_indices_tensor_d is not None
            if is_mamba_cache_all:
                state_indices_tensor_d_input = state_indices_tensor_d.gather(
                    1, block_idx_last_computed_token_d.unsqueeze(1)
                ).squeeze(1)
                state_indices_tensor_d_output = state_indices_tensor_d.gather(
                    1, block_idx_last_scheduled_token_d.unsqueeze(1)
                ).squeeze(1)
            else:
                state_indices_tensor_d_input = state_indices_tensor_d
                state_indices_tensor_d_output = state_indices_tensor_d
            # 2. Convolution sequence transformation
            conv_out_d = causal_conv1d_update(
                hidden_states_BC_d.transpose(0, 1),
                conv_state,
                conv_weights,
                self.conv1d.bias,
                self.activation,
                conv_state_indices=state_indices_tensor_d,
                block_idx_last_scheduled_token=block_idx_last_scheduled_token_d,
                initial_state_idx=block_idx_last_computed_token_d,
            ).transpose(0, 1)

            # 3. State Space Model sequence transformation.
            discrete_time_step_d, B_d, C_d = self._ssm_transform(
                conv_out_d.transpose(-2, -1)
            )
            time_proj_bias = self._time_proj_bias()

            # 4. Perform the recurrence y ← SSM(A, B, C, Δ)(x)
            scan_outputs_d = torch.empty_like(hidden_states_BC_d.transpose(0, 1))
            selective_state_update(
                ssm_state,
                conv_out_d.transpose(0, 1),
                discrete_time_step_d.transpose(0, 1),
                self.A,
                B_d,
                C_d,
                self.D,
                time_proj_bias,
                z=gate_d.transpose(0, 1),
                dt_softplus=True,
                state_batch_indices=state_indices_tensor_d_input,
                dst_state_batch_indices=state_indices_tensor_d_output,
                out=scan_outputs_d,
            )
            scan_outputs_d = scan_outputs_d.transpose(0, 1)

            ssm_outputs.insert(0, scan_outputs_d)

        scan_outputs_combined = (
            ssm_outputs[0] if len(ssm_outputs) == 1 else torch.cat(ssm_outputs, dim=-1)
        )

        # 5. Final output projection
        if self.is_lora_enabled:  # Lora kernel requires contiguous tensor.
            scan_outputs_combined = scan_outputs_combined.transpose(-2, -1).contiguous()
            out = self.out_proj(scan_outputs_combined)[0]
        else:
            out = self.out_proj(scan_outputs_combined.transpose(-2, -1))[0]

        output[:num_actual_tokens] = out