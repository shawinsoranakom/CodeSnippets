def get_num_flops_breakdown(
        self, ctx: ExecutionContext, per_gpu: bool = True
    ) -> dict[str, int]:
        """Calculate flops breakdown for FFN layers."""
        L, D, DI = self.num_hidden_layers, self.hidden_size, self.intermediate_size
        Lm, E, MI, S = (
            self.num_moe_layers,
            self.num_experts_per_tok,
            self.moe_intermediate_size,
            self.num_shared_experts,
        )
        T = ctx.total_num_tokens()

        Ld = L - Lm

        num_activated_tokens = T * E if E else 0

        if per_gpu:
            Ld //= self.pp_size
            Lm //= self.pp_size

            DI //= self.ffn_tp_size
            if MI is not None:
                MI //= self.ffn_tp_size
            if E:
                num_activated_tokens //= self.ffn_ep_size

        flops = {}

        # Dense FFN layers (SwiGLU: 3 linear layers: up, gate, down)
        if Ld:
            flops["dense_ffn"] = 2 * D * 3 * DI * T * Ld

        # MoE routed experts (each token activates E experts)
        if Lm and E:
            flops["routed_ffn"] = 2 * D * 3 * MI * num_activated_tokens * Lm

        # MoE shared experts (all S shared experts run for every token)
        if Lm and S:
            flops["shared_ffn"] = 2 * D * 3 * MI * S * T * Lm

        return flops