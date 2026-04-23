def _init_weights(self, module):
        """Initialize the weights"""
        # Wav2Vec2ForPreTraining last 2 linear layers need standard Linear init.
        if isinstance(module, Wav2Vec2ForPreTraining):
            module.project_hid.reset_parameters()
            module.project_q.reset_parameters()
        # gumbel softmax requires special init
        elif isinstance(module, Wav2Vec2GumbelVectorQuantizer):
            init.normal_(module.weight_proj.weight, mean=0.0, std=1)
            init.zeros_(module.weight_proj.bias)
            init.uniform_(module.codevectors)
        elif isinstance(module, Wav2Vec2PositionalConvEmbedding):
            init.normal_(
                module.conv.weight,
                mean=0,
                std=2 * math.sqrt(1 / (module.conv.kernel_size[0] * module.conv.in_channels)),
            )
            init.constant_(module.conv.bias, 0)
        elif isinstance(module, Wav2Vec2FeatureProjection):
            k = math.sqrt(1 / module.projection.in_features)
            init.uniform_(module.projection.weight, a=-k, b=k)
            init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)

            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, nn.Conv1d):
            init.kaiming_normal_(module.weight)

            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)