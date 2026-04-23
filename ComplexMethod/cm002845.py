def _init_weights(self, module):
        """Initialize the weights"""
        # initialize linear layer bias value according to a given probability value.
        if isinstance(module, (DFineForObjectDetection, DFineDecoder)):
            if module.class_embed is not None:
                for layer in module.class_embed:
                    prior_prob = self.config.initializer_bias_prior_prob or 1 / (self.config.num_labels + 1)
                    bias = float(-math.log((1 - prior_prob) / prior_prob))
                    init.xavier_uniform_(layer.weight)
                    init.constant_(layer.bias, bias)

            if module.bbox_embed is not None:
                for layer in module.bbox_embed:
                    init.constant_(layer.layers[-1].weight, 0)
                    init.constant_(layer.layers[-1].bias, 0)

            if hasattr(module, "reg_scale"):
                init.constant_(module.reg_scale, self.config.reg_scale)

            if hasattr(module, "up"):
                init.constant_(module.up, self.config.up)

        if isinstance(module, DFineMultiscaleDeformableAttention):
            init.constant_(module.sampling_offsets.weight, 0.0)
            default_dtype = torch.get_default_dtype()
            thetas = torch.arange(module.n_heads, dtype=torch.int64).to(default_dtype) * (
                2.0 * math.pi / module.n_heads
            )
            grid_init = torch.stack([thetas.cos(), thetas.sin()], -1)
            grid_init = grid_init / grid_init.abs().max(-1, keepdim=True).values
            grid_init = grid_init.reshape(module.n_heads, 1, 2).tile([1, sum(module.num_points_list), 1])
            scaling = torch.concat([torch.arange(1, n + 1) for n in module.num_points_list]).reshape(1, -1, 1)
            grid_init *= scaling
            init.copy_(module.sampling_offsets.bias, grid_init.flatten())

            init.constant_(module.attention_weights.weight, 0.0)
            init.constant_(module.attention_weights.bias, 0.0)

            num_points_scale = [1 / n for n in module.num_points_list for _ in range(n)]
            init.copy_(module.num_points_scale, torch.tensor(num_points_scale, dtype=torch.float32))

        if isinstance(module, DFineModel):
            prior_prob = self.config.initializer_bias_prior_prob or 1 / (self.config.num_labels + 1)
            bias = float(-math.log((1 - prior_prob) / prior_prob))
            init.xavier_uniform_(module.enc_score_head.weight)
            init.constant_(module.enc_score_head.bias, bias)

        if isinstance(module, (nn.Linear, nn.Conv2d, nn.BatchNorm2d)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)

        if isinstance(module, DFineGate):
            bias = float(-math.log((1 - 0.5) / 0.5))
            init.constant_(module.gate.bias, bias)
            init.constant_(module.gate.weight, 0)

        if isinstance(module, DFineLQE):
            init.constant_(module.reg_conf.layers[-1].bias, 0)
            init.constant_(module.reg_conf.layers[-1].weight, 0)

        if isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)

        if hasattr(module, "weight_embedding") and self.config.learn_initial_query:
            init.xavier_uniform_(module.weight_embedding.weight)
        if hasattr(module, "denoising_class_embed") and self.config.num_denoising > 0:
            init.xavier_uniform_(module.denoising_class_embed.weight)