def _init_weights(self, module):
        std = self.config.init_std

        if isinstance(module, MMGroundingDinoLearnedPositionEmbedding):
            init.uniform_(module.row_embeddings.weight)
            init.uniform_(module.column_embeddings.weight)
        elif isinstance(module, MMGroundingDinoMultiscaleDeformableAttention):
            init.constant_(module.sampling_offsets.weight, 0.0)
            default_dtype = torch.get_default_dtype()
            thetas = torch.arange(module.n_heads, dtype=torch.int64).to(default_dtype) * (
                2.0 * math.pi / module.n_heads
            )
            grid_init = torch.stack([thetas.cos(), thetas.sin()], -1)
            grid_init = (
                (grid_init / grid_init.abs().max(-1, keepdim=True)[0])
                .view(module.n_heads, 1, 1, 2)
                .repeat(1, module.n_levels, module.n_points, 1)
            )
            for i in range(module.n_points):
                grid_init[:, :, i, :] *= i + 1

            init.copy_(module.sampling_offsets.bias, grid_init.view(-1))
            init.constant_(module.attention_weights.weight, 0.0)
            init.constant_(module.attention_weights.bias, 0.0)
            init.xavier_uniform_(module.value_proj.weight)
            init.constant_(module.value_proj.bias, 0.0)
            init.xavier_uniform_(module.output_proj.weight)
            init.constant_(module.output_proj.bias, 0.0)
        elif isinstance(module, MMGroundingDinoBiMultiHeadAttention):
            init.xavier_uniform_(module.vision_proj.weight)
            init.zeros_(module.vision_proj.bias)
            init.xavier_uniform_(module.text_proj.weight)
            init.zeros_(module.text_proj.bias)
            init.xavier_uniform_(module.values_vision_proj.weight)
            init.zeros_(module.values_vision_proj.bias)
            init.xavier_uniform_(module.values_text_proj.weight)
            init.zeros_(module.values_text_proj.bias)
            init.xavier_uniform_(module.out_vision_proj.weight)
            init.zeros_(module.out_vision_proj.bias)
            init.xavier_uniform_(module.out_text_proj.weight)
            init.zeros_(module.out_text_proj.bias)
        elif isinstance(module, MMGroundingDinoFusionLayer):
            init.constant_(module.vision_param, 1e-4)
            init.constant_(module.text_param, 1e-4)
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, MMGroundingDinoMLPPredictionHead):
            init.constant_(module.layers[-1].weight, 0)
            init.constant_(module.layers[-1].bias, 0)

        if hasattr(module, "reference_points") and not self.config.two_stage:
            init.xavier_uniform_(module.reference_points.weight, gain=1.0)
            init.constant_(module.reference_points.bias, 0.0)
        if hasattr(module, "level_embed"):
            init.normal_(module.level_embed)
        if isinstance(module, MMGroundingDinoContrastiveEmbedding):
            init.constant_(module.bias, -math.log((1 - 0.01) / 0.01))