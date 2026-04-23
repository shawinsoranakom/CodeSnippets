def _init_weights(self, module):
        super()._init_weights(module)
        if isinstance(module, EdgeTamVideoModel):
            if module.no_memory_positional_encoding is not None:
                init.zeros_(module.no_memory_positional_encoding)
            if module.memory_temporal_positional_encoding is not None:
                init.zeros_(module.memory_temporal_positional_encoding)
            if module.no_object_pointer is not None:
                init.zeros_(module.no_object_pointer)
            if module.occlusion_spatial_embedding_parameter is not None:
                init.zeros_(module.occlusion_spatial_embedding_parameter)
        if isinstance(module, EdgeTamVideoMemoryFuserCXBlock):
            if module.scale is not None:
                init.zeros_(module.scale)
        elif isinstance(module, EdgeTamVideoVisionRotaryEmbedding):
            inv_freq = module.create_inv_freq()
            init.copy_(module.rope_embeddings_cos, inv_freq.cos())
            init.copy_(module.rope_embeddings_sin, inv_freq.sin())
        elif isinstance(module, EdgeTamVideoPositionalEmbedding):
            init.normal_(module.positional_embedding, std=module.scale)
        if isinstance(module, EdgeTamVideoVisionRotaryEmbedding):
            inv_freq = module.create_inv_freq()
            init.copy_(module.rope_embeddings_cos, inv_freq.cos())
            init.copy_(module.rope_embeddings_sin, inv_freq.sin())