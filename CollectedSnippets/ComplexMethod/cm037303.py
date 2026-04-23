def get_write_bytes_breakdown(
        self, ctx: ExecutionContext, per_gpu: bool = True
    ) -> dict[str, int]:
        """Calculate write memory traffic for FFN layers."""
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

        write_bytes = {}

        # Dense FFN layers
        if Ld:
            write_bytes["dense_up_gate_output"] = int(
                2 * T * DI * self.activation_byte_size * Ld
            )
            write_bytes["dense_silu_output"] = int(
                T * DI * self.activation_byte_size * Ld
            )
            write_bytes["dense_down_output"] = int(
                T * D * self.activation_byte_size * Ld
            )

        # MoE outputs
        if Lm:
            if E:
                write_bytes["routed_up_gate_output"] = int(
                    2 * num_activated_tokens * MI * self.activation_byte_size * Lm
                )
                write_bytes["routed_silu_output"] = int(
                    num_activated_tokens * MI * self.activation_byte_size * Lm
                )
                write_bytes["routed_down_output"] = int(
                    num_activated_tokens * D * self.activation_byte_size * Lm
                )
            if S:
                write_bytes["shared_up_gate_output"] = int(
                    2 * T * S * MI * self.activation_byte_size * Lm
                )
                write_bytes["shared_silu_output"] = int(
                    T * S * MI * self.activation_byte_size * Lm
                )
                write_bytes["shared_down_output"] = int(
                    T * S * D * self.activation_byte_size * Lm
                )

        return write_bytes