def forward(
        self,
        positions: torch.Tensor,
        hidden_states: torch.Tensor,
        residual: torch.Tensor | None,
    ) -> torch.Tensor:
        if residual is None:
            residual = hidden_states.clone()
            hidden_states = self.input_layernorm(hidden_states)
        else:
            hidden_states, residual = self.input_layernorm(hidden_states, residual)

        hidden_states = self.self_attn(
            positions=positions,
            hidden_states=hidden_states,
        )

        if (
            self.routed_scaling_factor is not None
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

        if self.sandwich_norm:
            hidden_states = self.post_attention_layernorm(hidden_states)
            hidden_states, residual = self.pre_mlp_layernorm(hidden_states, residual)
        else:
            hidden_states, residual = self.post_attention_layernorm(
                hidden_states, residual
            )

        # Fully Connected
        hidden_states = self.mlp(hidden_states)

        if (
            self.routed_scaling_factor is not None
            and isinstance(self.mlp, OpenPanguMLP)
            and hidden_states.dtype == torch.float16
        ):
            hidden_states *= 1.0 / self.routed_scaling_factor

        if self.sandwich_norm:
            hidden_states = self.post_mlp_layernorm(hidden_states)

        return hidden_states, residual