def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, (nn.Conv1d, nn.ConvTranspose1d)):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, MimiLayerScale):
            init.constant_(module.scale, self.config.layer_scale_initial_scale)
        elif isinstance(module, MimiConv1d):
            kernel_size = module.conv.kernel_size[0]
            stride = module.conv.stride[0]
            dilation = module.conv.dilation[0]
            kernel_size = (kernel_size - 1) * dilation + 1
            init.constant_(module.stride, stride)
            init.constant_(module.kernel_size, kernel_size)
            init.constant_(module.padding_total, kernel_size - stride)
        elif isinstance(module, MimiEuclideanCodebook):
            init.ones_(module.initialized)
            init.ones_(module.cluster_usage)
            init.zeros_(module.embed_sum)
        elif isinstance(module, MimiRotaryEmbedding):
            rope_fn = (
                ROPE_INIT_FUNCTIONS[module.rope_type]
                if module.rope_type != "default"
                else module.compute_default_rope_parameters
            )
            buffer_value, _ = rope_fn(module.config)
            init.copy_(module.inv_freq, buffer_value)
            init.copy_(module.original_inv_freq, buffer_value)