def get_read_bytes_breakdown(
        self, ctx: ExecutionContext, per_gpu: bool = True
    ) -> dict[str, int]:
        """Calculate read memory traffic for FFN layers."""
        L, D, DI = self.num_hidden_layers, self.hidden_size, self.intermediate_size
        Lm, E, MI, S = (
            self.num_moe_layers,
            self.num_experts_per_tok,
            self.moe_intermediate_size,
            self.num_shared_experts,
        )
        T = ctx.total_num_tokens()
        num_experts = self.num_experts

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
            if num_experts is not None:
                num_experts //= self.ffn_ep_size

        read_bytes = {}

        # Dense FFN layers (3 GEMMs: up, gate, down projections + SiLU activation)
        if Ld:
            read_bytes["dense_up_gate_input"] = int(
                T * D * self.activation_byte_size * Ld
            )
            read_bytes["dense_up_gate_weights"] = int(
                2 * D * DI * self.weight_byte_size * Ld
            )
            read_bytes["dense_silu_input"] = int(
                2 * T * DI * self.activation_byte_size * Ld
            )
            read_bytes["dense_down_input"] = int(
                T * DI * self.activation_byte_size * Ld
            )
            read_bytes["dense_down_weights"] = int(D * DI * self.weight_byte_size * Ld)

        if Lm:
            # MoE routed expert reads
            if E:
                # FIXME: Assume perfect load balancing for now.
                num_activated_experts = min(num_activated_tokens, num_experts)

                read_bytes["routed_up_gate_input"] = int(
                    num_activated_tokens * D * self.activation_byte_size * Lm
                )
                read_bytes["routed_up_gate_weights"] = int(
                    2 * D * MI * num_activated_experts * self.weight_byte_size * Lm
                )
                read_bytes["routed_silu_input"] = int(
                    2 * num_activated_tokens * MI * self.activation_byte_size * Lm
                )
                read_bytes["routed_down_input"] = int(
                    num_activated_tokens * MI * self.activation_byte_size * Lm
                )
                read_bytes["routed_down_weights"] = int(
                    D * MI * num_activated_experts * self.weight_byte_size * Lm
                )

            # MoE shared expert reads
            if S:
                read_bytes["shared_up_gate_input"] = int(
                    T * D * self.activation_byte_size * Lm
                )
                read_bytes["shared_up_gate_weights"] = int(
                    2 * D * MI * S * self.weight_byte_size * Lm
                )
                read_bytes["shared_silu_input"] = int(
                    2 * T * MI * S * self.activation_byte_size * Lm
                )
                read_bytes["shared_down_input"] = int(
                    T * MI * self.activation_byte_size * Lm
                )
                read_bytes["shared_down_weights"] = int(
                    D * MI * S * self.weight_byte_size * Lm
                )

        return read_bytes