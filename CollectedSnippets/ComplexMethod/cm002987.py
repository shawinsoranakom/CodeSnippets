def _init_weights(self, module):
        """Initialize the weights"""
        super()._init_weights(module)
        if isinstance(module, LayoutLMv2SelfAttention):
            if self.config.fast_qkv:
                init.zeros_(module.q_bias)
                init.zeros_(module.v_bias)
        elif isinstance(module, LayoutLMv2Embeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, LayoutLMv2VisualBackbone):
            num_channels = len(module.cfg.MODEL.PIXEL_MEAN)
            init.copy_(module.pixel_mean, torch.Tensor(module.cfg.MODEL.PIXEL_MEAN).view(num_channels, 1, 1))
            init.copy_(module.pixel_std, torch.Tensor(module.cfg.MODEL.PIXEL_STD).view(num_channels, 1, 1))
        elif isinstance(module, LayoutLMv2Model):
            if hasattr(module, "visual_segment_embedding"):
                init.normal_(module.visual_segment_embedding, mean=0.0, std=self.config.initializer_range)
        # We check the existence of each one since detectron2 seems to do weird things
        elif isinstance(module, detectron2.layers.FrozenBatchNorm2d):
            init.ones_(module.weight)
            init.zeros_(module.bias)
            init.zeros_(module.running_mean)
            init.constant_(module.running_var, 1.0 - module.eps)