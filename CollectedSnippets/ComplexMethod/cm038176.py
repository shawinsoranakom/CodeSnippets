def permute_qk_weight_for_rotary(
        self,
        name: str,
        loaded_weight: torch.Tensor,
    ) -> tuple[str, torch.Tensor]:
        modules = name.split(".")
        # Permute Q/K weights and corresponding scales for rotary embedding.
        # This pathway is validated against modelopt and compressed-tensors ckpts,
        # and for per-tensor, per-group (e.g. GPTQ), and per-channel quant schemes.
        # Note: permutations are not feasible only for per-block (e.g. DeepSeek 128x128)
        # For per-block quantization, consider not quantizing q/k_proj.
        is_weight = modules[-1] in ("weight", "weight_packed")
        is_weight_scale = (
            modules[-1] == "weight_scale"
            and loaded_weight.numel() > 1  # no need to permute per-tensor scales
        )
        is_k_proj = "wk" in modules or "k_proj" in modules
        is_q_proj = "wq" in modules or "q_proj" in modules

        if (is_weight or is_weight_scale) and (is_k_proj or is_q_proj):
            original_ndim = loaded_weight.ndim
            if original_ndim == 1:
                loaded_weight = loaded_weight.unsqueeze(-1)

            f_out, f_in = loaded_weight.shape
            n_heads = (
                self.config.num_key_value_heads
                if is_k_proj
                else self.config.num_attention_heads
            )
            loaded_weight = (
                loaded_weight.view(n_heads, f_out // n_heads // 2, 2, f_in)
                .transpose(1, 2)
                .reshape(f_out, f_in)
            )

            if original_ndim == 1:
                loaded_weight = loaded_weight.squeeze(-1)

        return name, loaded_weight