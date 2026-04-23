def _init_weights(self, module):
        std = self.config.init_std
        xavier_std = self.config.init_xavier_std

        if isinstance(module, MaskFormerDetrMaskHeadSmallConv):
            # MaskFormerDetrMaskHeadSmallConv uses kaiming initialization for all its Conv2d layers
            for m in module.modules():
                if isinstance(m, nn.Conv2d):
                    init.kaiming_uniform_(m.weight, a=1)
                    if m.bias is not None:
                        init.constant_(m.bias, 0)
        elif isinstance(module, MaskFormerDetrMHAttentionMap):
            init.zeros_(module.k_proj.bias)
            init.zeros_(module.q_proj.bias)
            init.xavier_uniform_(module.k_proj.weight, gain=xavier_std)
            init.xavier_uniform_(module.q_proj.weight, gain=xavier_std)
        elif isinstance(module, MaskFormerDetrLearnedPositionEmbedding):
            init.uniform_(module.row_embeddings.weight)
            init.uniform_(module.column_embeddings.weight)
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.ones_(module.weight)
            init.zeros_(module.bias)