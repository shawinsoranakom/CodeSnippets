def _init_weights(self, module):
        std = self.config.init_std
        xavier_std = self.config.init_xavier_std

        if isinstance(module, DabDetrMHAttentionMap):
            init.zeros_(module.k_linear.bias)
            init.zeros_(module.q_linear.bias)
            init.xavier_uniform_(module.k_linear.weight, gain=xavier_std)
            init.xavier_uniform_(module.q_linear.weight, gain=xavier_std)
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, DabDetrForObjectDetection):
            init.constant_(module.bbox_predictor.layers[-1].weight, 0)
            init.constant_(module.bbox_predictor.layers[-1].bias, 0)

            # init prior_prob setting for focal loss
            prior_prob = self.config.initializer_bias_prior_prob or 1 / (self.config.num_labels + 1)
            bias_value = -math.log((1 - prior_prob) / prior_prob)
            init.constant_(module.class_embed.bias, bias_value)
        elif isinstance(module, nn.PReLU):
            module.reset_parameters()