def _estimate_kv_cache_bytes(
        self, n_ctx: int, cache_type_kv: Optional[str] = None
    ) -> int:
        """Estimate KV cache VRAM for a given context length.

        Uses 5-path architecture-aware estimation:
          1. MLA      -- compressed KV latent + RoPE, K-only (no separate V)
          2. Hybrid   -- only attention layers need KV (Mamba layers don't)
          3. SWA      -- sliding-window layers cache min(ctx, window) tokens
          4. GQA      -- standard full KV with explicit key/value dimensions
          5. Legacy   -- fallback using embed // n_heads

        Returns 0 if metadata is insufficient for estimation.
        """
        if not self._can_estimate_kv() or n_ctx <= 0:
            return 0

        n_layers = self._n_layers  # type: ignore[assignment]
        n_kv = self._n_kv_heads or self._n_heads or 1  # type: ignore[assignment]

        # Bytes per element depends on KV cache quantization
        bpe = {
            "f32": 4.0,
            "f16": 2.0,
            "bf16": 2.0,
            "q8_0": 34 / 32,
            "q5_1": 0.75,
            "q5_0": 0.6875,
            "q4_1": 0.625,
            "q4_0": 0.5625,
            "iq4_nl": 0.5625,
        }.get(cache_type_kv or "f16", 2.0)

        # Path 1: MLA (DeepSeek-V2/V3, GLM-4.7, GLM-5, Kimi-K2.5)
        # MLA stores one compressed KV latent per token/layer (shared across heads).
        # V is reconstructed from the latent on the fly -- no separate V cache.
        # key_length = kv_lora_rank + rope_dim (the full compressed representation).
        # MLA GGUFs set head_count_kv=1; default to 1 if absent to avoid
        # falling back to n_heads (e.g., 128 for DeepSeek-V3) which would 128x.
        if self._kv_lora_rank is not None:
            n_kv_mla = self._n_kv_heads or 1
            rope_dim = self._key_length_mla or 64
            key_len = self._kv_key_length or (self._kv_lora_rank + rope_dim)
            return int(n_layers * n_ctx * n_kv_mla * key_len * bpe)

        key_len = self._kv_key_length
        val_len = self._kv_value_length

        # Path 2: Hybrid Mamba/Attention (Qwen3.5-27B, Qwen3.5-35B-A3B)
        # Only 1 in N layers is attention; the rest are Mamba (no KV cache).
        if (
            self._ssm_inner_size is not None
            and self._full_attention_interval is not None
        ):
            fai = self._full_attention_interval
            n_attn = -(-n_layers // fai) if fai > 0 else n_layers  # ceiling division
            if key_len is not None and val_len is not None:
                return int(n_attn * n_ctx * n_kv * (key_len + val_len) * bpe)
            head_dim = self._embedding_length // self._n_heads if self._n_heads else 128  # type: ignore[operator]
            return int(n_attn * n_ctx * n_kv * 2 * head_dim * bpe)

        # Path 3: Sliding Window (Gemma-3, gpt-oss)
        # SWA layers only cache min(ctx, window) tokens; global layers cache full ctx.
        # Most SWA architectures use few global layers (e.g., Gemma-3 uses 1 in 6).
        # Without an explicit field, we conservatively assume 1/4 of layers are global
        # which is still far more accurate than the legacy formula (which ignores SWA).
        if (
            self._sliding_window is not None
            and self._sliding_window > 0
            and key_len is not None
            and val_len is not None
        ):
            swa = self._sliding_window
            n_global = max(1, n_layers // 4)
            n_swa = n_layers - n_global
            kv_per_token = n_kv * (key_len + val_len) * bpe
            return int(
                n_global * n_ctx * kv_per_token + n_swa * min(n_ctx, swa) * kv_per_token
            )

        # Path 4: Standard GQA with explicit key/value dimensions
        if key_len is not None and val_len is not None:
            return int(n_layers * n_ctx * n_kv * (key_len + val_len) * bpe)

        # Path 5: Legacy fallback (old GGUFs without explicit dimensions)
        head_dim = self._embedding_length // self._n_heads if self._n_heads else 128  # type: ignore[operator]
        return int(2 * n_kv * head_dim * n_layers * n_ctx * bpe)