def _init_weights(self, module):
        def linear_init_(module_to_init):
            bound = 1 / math.sqrt(module_to_init.weight.shape[0])
            init.uniform_(module_to_init.weight, -bound, bound)
            if hasattr(module_to_init, "bias") and module_to_init.bias is not None:
                init.uniform_(module_to_init.bias, -bound, bound)

        if isinstance(module, OmDetTurboEncoderLayer):
            linear_init_(module.fc1)
            linear_init_(module.fc2)
        elif isinstance(module, OmDetTurboDecoder):
            init.constant_(module.encoder_bbox_head.layers[-1].weight, 0.0)
            init.constant_(module.encoder_bbox_head.layers[-1].bias, 0.0)
            for mlp in module.decoder_bbox_head:
                init.constant_(mlp.layers[-1].weight, 0.0)
                init.constant_(mlp.layers[-1].bias, 0.0)
            linear_init_(module.encoder_vision_features[0])
            init.xavier_uniform_(module.encoder_vision_features[0].weight)
            if module.learn_initial_query:
                init.xavier_uniform_(module.tgt_embed.weight)
            init.xavier_uniform_(module.query_position_head.layers[0].weight)
            init.xavier_uniform_(module.query_position_head.layers[1].weight)
            for layer in module.channel_projection_layers:
                init.xavier_uniform_(layer[0].weight)
        elif isinstance(module, OmDetTurboLanguageBackbone):
            init.normal_(module.text_projection, std=self.config.text_projection_in_dim**-0.5)
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=self.config.init_std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            init.ones_(module.weight)
            init.zeros_(module.bias)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)