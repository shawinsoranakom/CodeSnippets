def _init_weights(self, module):
        """
        Initialize BLT weights following the original ByteLatentTransformer:

        - Most weights are drawn from a truncated normal.
        - Scale is ~ 1 / sqrt(model_dim) (or 1 / sqrt(hidden_dim) for FFN outputs).
        - Norm layers are set to weight = 1, bias = 0.
        """
        class_name = module.__class__.__name__

        # Norms: RMSNorm / LayerNorm
        if isinstance(module, (BltRMSNorm, nn.LayerNorm)) or "RMSNorm" in class_name or "LayerNorm" in class_name:
            if getattr(module, "weight", None) is not None:
                init.ones_(module.weight)
            if getattr(module, "bias", None) is not None:
                init.zeros_(module.bias)
            return

        # Embeddings (encoder / patcher / hash embeddings)
        if isinstance(module, nn.Embedding):
            hidden_size = getattr(self.config, "hidden_size", None)
            if hidden_size is None and hasattr(self.config, "encoder_config"):
                hidden_size = getattr(self.config.encoder_config, "hidden_size", None)
            if hidden_size is None:
                hidden_size = module.embedding_dim

            std = hidden_size**-0.5
            init.trunc_normal_(
                module.weight,
                mean=0.0,
                std=std,
                a=-3 * std,
                b=3 * std,
            )
            if module.padding_idx is not None:
                init.zeros_(module.weight[module.padding_idx])
            return

        # Self-attention / cross-attention projections
        if isinstance(module, (BltSelfAttention, BltCrossAttention)) or class_name in (
            "MllamaTextSelfAttention",
            "MllamaTextCrossAttention",
        ):
            dim = getattr(self.config, "hidden_size", None)
            if dim is None and hasattr(module, "hidden_size"):
                dim = module.hidden_size
            if dim is None:
                for name in ("q_proj", "k_proj", "v_proj", "o_proj", "dense"):
                    proj = getattr(module, name, None)
                    if proj is not None and hasattr(proj, "weight"):
                        dim = proj.weight.shape[-1]
                        break
            if dim is None:
                return

            std = dim**-0.5

            # Input projections (q, k, v)
            for proj_name in ("q_proj", "k_proj", "v_proj"):
                proj = getattr(module, proj_name, None)
                if proj is not None and hasattr(proj, "weight"):
                    init.trunc_normal_(
                        proj.weight,
                        mean=0.0,
                        std=std,
                        a=-3 * std,
                        b=3 * std,
                    )
                    if getattr(proj, "bias", None) is not None:
                        init.zeros_(proj.bias)

            # Output projection: o_proj or dense
            o_proj = getattr(module, "o_proj", getattr(module, "dense", None))
            if o_proj is not None and hasattr(o_proj, "weight"):
                init.trunc_normal_(
                    o_proj.weight,
                    mean=0.0,
                    std=std,
                    a=-3 * std,
                    b=3 * std,
                )
                if getattr(o_proj, "bias", None) is not None:
                    init.zeros_(o_proj.bias)
            return

        # MLP / FFN blocks
        if isinstance(module, BltMLP) or class_name == "MllamaTextMLP":
            hidden_size = getattr(self.config, "hidden_size", None)
            if hidden_size is None and hasattr(self.config, "decoder_config"):
                hidden_size = getattr(self.config.decoder_config, "hidden_size", None)
            if hidden_size is None and hasattr(self.config, "encoder_config"):
                hidden_size = getattr(self.config.encoder_config, "hidden_size", None)

            # Input-side std
            in_std = None
            if hidden_size is not None:
                in_std = hidden_size**-0.5

            gate_proj = getattr(module, "gate_proj", getattr(module, "fc1", None))
            up_proj = getattr(module, "up_proj", None)
            down_proj = getattr(module, "down_proj", getattr(module, "fc2", None))

            # gate / input projections
            for proj in (gate_proj, up_proj):
                if proj is not None and hasattr(proj, "weight"):
                    std = in_std or (proj.weight.shape[1] ** -0.5)
                    init.trunc_normal_(
                        proj.weight,
                        mean=0.0,
                        std=std,
                        a=-3 * std,
                        b=3 * std,
                    )
                    if getattr(proj, "bias", None) is not None:
                        init.zeros_(proj.bias)

            # output/ down projections
            if down_proj is not None and hasattr(down_proj, "weight"):
                hidden_dim = down_proj.weight.shape[1]
                out_std = hidden_dim**-0.5
                init.trunc_normal_(
                    down_proj.weight,
                    mean=0.0,
                    std=out_std,
                    a=-3 * out_std,
                    b=3 * out_std,
                )
                if getattr(down_proj, "bias", None) is not None:
                    init.zeros_(down_proj.bias)
            return

        # Generic Linear layers (projections, lm_head, etc.)
        if isinstance(module, nn.Linear):
            fan_in = module.in_features
            std = fan_in**-0.5
            init.trunc_normal_(
                module.weight,
                mean=0.0,
                std=std,
                a=-3 * std,
                b=3 * std,
            )
            if module.bias is not None:
                init.zeros_(module.bias)
            return

        if isinstance(module, BltRotaryEmbedding):
            rope_fn = (
                ROPE_INIT_FUNCTIONS[module.rope_type]
                if module.rope_type != "default"
                else module.compute_default_rope_parameters
            )
            buffer_value, _ = rope_fn(module.config)
            init.copy_(module.inv_freq, buffer_value)
            init.copy_(module.original_inv_freq, buffer_value)