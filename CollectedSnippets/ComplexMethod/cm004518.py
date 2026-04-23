def _init_weights(self, module):
        classname = module.__class__.__name__
        if classname.find("Linear") != -1:
            if getattr(module, "weight", None) is not None:
                if self.config.initializer_std is None:
                    fan_out, fan_in = module.weight.shape
                    std = np.sqrt(1.0 / float(fan_in + fan_out))
                else:
                    std = self.config.initializer_std
                init.normal_(module.weight, std=std)
            if getattr(module, "bias", None) is not None:
                init.constant_(module.bias, 0.0)
        elif classname == "FunnelRelMultiheadAttention":
            init.uniform_(module.r_w_bias, b=self.config.initializer_range)
            init.uniform_(module.r_r_bias, b=self.config.initializer_range)
            init.uniform_(module.r_kernel, b=self.config.initializer_range)
            init.uniform_(module.r_s_bias, b=self.config.initializer_range)
            init.uniform_(module.seg_embed, b=self.config.initializer_range)
        elif classname == "FunnelEmbeddings":
            std = 1.0 if self.config.initializer_std is None else self.config.initializer_std
            init.normal_(module.word_embeddings.weight, std=std)
            if module.word_embeddings.padding_idx is not None:
                init.zeros_(module.word_embeddings.weight[module.word_embeddings.padding_idx])