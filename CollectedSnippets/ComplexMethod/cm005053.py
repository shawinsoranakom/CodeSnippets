def _init_weights(self, module: nn.Linear | nn.Conv2d | nn.LayerNorm) -> None:
        """Initialize the weights"""
        super()._init_weights(module)
        if isinstance(module, FlavaMaskedPredictionHead):
            init.zeros_(module.bias)
        elif isinstance(module, FlavaImageEmbeddings):
            init.zeros_(module.cls_token)
            init.zeros_(module.position_embeddings)
            if module.mask_token is not None:
                init.zeros_(module.mask_token)
        elif isinstance(module, FlavaTextEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
            init.zeros_(module.token_type_ids)
        elif isinstance(module, FlavaMultimodalModel):
            if module.use_cls_token:
                init.zeros_(module.cls_token)
        elif isinstance(module, FlavaModel):
            init.constant_(module.logit_scale, self.config.logit_scale_init_value)