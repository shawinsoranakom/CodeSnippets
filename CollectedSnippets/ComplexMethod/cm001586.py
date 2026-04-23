def undo_hijack(self, m):
        conditioner = getattr(m, 'conditioner', None)
        if conditioner:
            for i in range(len(conditioner.embedders)):
                embedder = conditioner.embedders[i]
                if isinstance(embedder, (sd_hijack_open_clip.FrozenOpenCLIPEmbedderWithCustomWords, sd_hijack_open_clip.FrozenOpenCLIPEmbedder2WithCustomWords)):
                    embedder.wrapped.model.token_embedding = embedder.wrapped.model.token_embedding.wrapped
                    conditioner.embedders[i] = embedder.wrapped
                if isinstance(embedder, sd_hijack_clip.FrozenCLIPEmbedderForSDXLWithCustomWords):
                    embedder.wrapped.transformer.text_model.embeddings.token_embedding = embedder.wrapped.transformer.text_model.embeddings.token_embedding.wrapped
                    conditioner.embedders[i] = embedder.wrapped

            if hasattr(m, 'cond_stage_model'):
                delattr(m, 'cond_stage_model')

        elif type(m.cond_stage_model) == sd_hijack_xlmr.FrozenXLMREmbedderWithCustomWords:
            m.cond_stage_model = m.cond_stage_model.wrapped

        elif type(m.cond_stage_model) == sd_hijack_clip.FrozenCLIPEmbedderWithCustomWords:
            m.cond_stage_model = m.cond_stage_model.wrapped

            model_embeddings = m.cond_stage_model.transformer.text_model.embeddings
            if type(model_embeddings.token_embedding) == EmbeddingsWithFixes:
                model_embeddings.token_embedding = model_embeddings.token_embedding.wrapped
        elif type(m.cond_stage_model) == sd_hijack_open_clip.FrozenOpenCLIPEmbedderWithCustomWords:
            m.cond_stage_model.wrapped.model.token_embedding = m.cond_stage_model.wrapped.model.token_embedding.wrapped
            m.cond_stage_model = m.cond_stage_model.wrapped

        undo_optimizations()
        undo_weighted_forward(m)

        self.apply_circular(False)
        self.layers = None
        self.clip = None