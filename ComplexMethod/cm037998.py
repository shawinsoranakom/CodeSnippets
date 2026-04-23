def reshape_fairseq2_weights(
        self,
        name: str,
        loaded_weight: torch.Tensor,
        params: dict[str, Parameter],
    ) -> tuple[str, torch.Tensor]:
        """Reshape fairseq2's weights."""

        def permute(w: torch.Tensor, n_heads: int) -> torch.Tensor:
            attn_in = self.config.head_dim * n_heads
            # check for a sharded weight on dim 0
            if attn_in // self.tp_size == w.size()[0]:
                attn_in //= self.tp_size
                n_heads //= self.tp_size
            attn_out = self.config.hidden_size
            return (
                w.view(n_heads, attn_in // n_heads // 2, 2, attn_out)
                .transpose(1, 2)
                .reshape(attn_in, attn_out)
            )

        modules = name.split(".")

        # rotary embeds should be sliced
        if "k_proj" in modules:
            loaded_weight = permute(loaded_weight, self.config.num_key_value_heads)

        elif "q_proj" in modules:
            loaded_weight = permute(loaded_weight, self.config.num_attention_heads)

        # We make the loaded weights compatible with both
        # full checkpoints and tp sharded checkpoints.
        # Embeddings are repeated to fit the vocab size.
        # Other weights are flagged for the weight_loader calls.
        if any(emb in modules for emb in ["embed_tokens", "lm_head"]):
            # Embeddings are sharded on dim 0
            dim = 0
            # In fairseq2, vocab size has to be divisible by tp_size
            # so we don't worry about padding
            if self.tp_size > 1 and loaded_weight.shape[dim] < self.config.vocab_size:
                assert (
                    loaded_weight.shape[dim] * self.tp_size == self.config.vocab_size
                ), "vocab_size should be divisible by tp_size."
                repeats = [1] * len(loaded_weight.size())
                repeats[dim] = self.tp_size
                # repeat to match vocab size and to be easily 'narrow'able
                loaded_weight = loaded_weight.repeat(repeats)
                set_weight_attrs(params[name], {"is_sharded_weight": False})
                # if embeddings are sharded, the rest is too
                if "embed_tokens" in modules:
                    self.flag_sharded_weights(params)

        return name, loaded_weight