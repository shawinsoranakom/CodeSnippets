def forward(
        self,
        positions: torch.Tensor,
        hidden_states: torch.Tensor,
        residual: torch.Tensor | None,
        llama_4_scaling: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        # Self Attention
        if residual is None:
            residual = hidden_states.clone()
            hidden_states = self.input_layernorm(hidden_states)
        else:
            hidden_states, residual = self.input_layernorm(hidden_states, residual)

        attn_kwargs = {
            "positions": positions,
            "hidden_states": hidden_states,
        }
        if not self.use_mha:
            attn_kwargs["llama_4_scaling"] = llama_4_scaling
        hidden_states = self.self_attn(**attn_kwargs)

        if (
            not isinstance(self.self_attn, DeepseekAttention)
            and hidden_states.dtype == torch.float16
        ):
            # Fix FP16 overflow
            # We scale both hidden_states and residual before
            # rmsnorm, and rmsnorm result would not affect by scale.
            hidden_states *= 1.0 / self.routed_scaling_factor
            if self.layer_idx == 0:
                # The residual is shared by all layers, we only scale it on
                # first layer.
                residual *= 1.0 / self.routed_scaling_factor

        # Fully Connected
        hidden_states, residual = self.post_attention_layernorm(hidden_states, residual)
        hidden_states = self.mlp(hidden_states)

        if self.is_layer_sparse:
            hidden_states = self.post_mlp_layernorm(hidden_states)

        if isinstance(self.mlp, AXK1MLP) and hidden_states.dtype == torch.float16:
            # Fix FP16 overflow
            # Scaling the AXK1MLP output, it is the input of
            # input_layernorm of next decoder layer.
            # The scaling of AXK1MOE output would be done in the forward
            # of AXK1MOE
            hidden_states *= 1.0 / self.routed_scaling_factor

        return hidden_states, residual