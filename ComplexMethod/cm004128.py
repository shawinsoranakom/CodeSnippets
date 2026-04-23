def _init_weights(self, module):
        super()._init_weights(module)

        if isinstance(module, LwDetrMultiscaleDeformableAttention):
            init.constant_(module.sampling_offsets.weight, 0.0)
            thetas = torch.arange(module.n_heads, dtype=torch.int64).float() * (2.0 * math.pi / module.n_heads)
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
        if hasattr(module, "level_embed"):
            init.normal_(module.level_embed)
        if hasattr(module, "refpoint_embed") and module.refpoint_embed is not None:
            init.constant_(module.refpoint_embed.weight, 0)
        if hasattr(module, "class_embed") and module.class_embed is not None:
            prior_prob = 0.01
            bias_value = -math.log((1 - prior_prob) / prior_prob)
            init.constant_(module.class_embed.bias, bias_value)
        if hasattr(module, "bbox_embed") and module.bbox_embed is not None:
            init.constant_(module.bbox_embed.layers[-1].weight, 0)
            init.constant_(module.bbox_embed.layers[-1].bias, 0)