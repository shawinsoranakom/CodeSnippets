def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.Linear):
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
        elif module.__class__.__name__ == "Snake1d":
            init.ones_(module.alpha)
        elif isinstance(module, nn.ConvTranspose1d):
            module.reset_parameters()
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=0.02)
        elif isinstance(module, HiggsAudioV2TokenizerModel):
            # The conv1d are not handled correctly, as `self.acoustic_encoder/decoder` are initialized from a PreTrainedModel,
            # but then only the submodules are used (which are not PreTrainedModels...) -> here we reinit them as in DacModel
            for submodule in module.acoustic_encoder.modules():
                if isinstance(submodule, nn.Conv1d):
                    init.trunc_normal_(submodule.weight, std=0.02)
                    init.constant_(submodule.bias, 0)
            for submodule in module.acoustic_decoder.modules():
                if isinstance(submodule, nn.Conv1d):
                    init.trunc_normal_(submodule.weight, std=0.02)
                    init.constant_(submodule.bias, 0)
        elif isinstance(module, HiggsAudioV2TokenizerEuclideanCodebook):
            init.copy_(module.inited, torch.Tensor([True]))
            init.zeros_(module.cluster_size)
            init.zeros_(module.embed)
            init.zeros_(module.embed_avg)