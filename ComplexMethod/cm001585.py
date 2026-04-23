def hijack(self, m):
        conditioner = getattr(m, 'conditioner', None)
        if conditioner:
            text_cond_models = []

            for i in range(len(conditioner.embedders)):
                embedder = conditioner.embedders[i]
                typename = type(embedder).__name__
                if typename == 'FrozenOpenCLIPEmbedder':
                    embedder.model.token_embedding = EmbeddingsWithFixes(embedder.model.token_embedding, self)
                    conditioner.embedders[i] = sd_hijack_open_clip.FrozenOpenCLIPEmbedderWithCustomWords(embedder, self)
                    text_cond_models.append(conditioner.embedders[i])
                if typename == 'FrozenCLIPEmbedder':
                    model_embeddings = embedder.transformer.text_model.embeddings
                    model_embeddings.token_embedding = EmbeddingsWithFixes(model_embeddings.token_embedding, self)
                    conditioner.embedders[i] = sd_hijack_clip.FrozenCLIPEmbedderForSDXLWithCustomWords(embedder, self)
                    text_cond_models.append(conditioner.embedders[i])
                if typename == 'FrozenOpenCLIPEmbedder2':
                    embedder.model.token_embedding = EmbeddingsWithFixes(embedder.model.token_embedding, self, textual_inversion_key='clip_g')
                    conditioner.embedders[i] = sd_hijack_open_clip.FrozenOpenCLIPEmbedder2WithCustomWords(embedder, self)
                    text_cond_models.append(conditioner.embedders[i])

            if len(text_cond_models) == 1:
                m.cond_stage_model = text_cond_models[0]
            else:
                m.cond_stage_model = conditioner

        if type(m.cond_stage_model) == xlmr.BertSeriesModelWithTransformation or type(m.cond_stage_model) == xlmr_m18.BertSeriesModelWithTransformation:
            model_embeddings = m.cond_stage_model.roberta.embeddings
            model_embeddings.token_embedding = EmbeddingsWithFixes(model_embeddings.word_embeddings, self)
            m.cond_stage_model = sd_hijack_xlmr.FrozenXLMREmbedderWithCustomWords(m.cond_stage_model, self)

        elif type(m.cond_stage_model) == ldm.modules.encoders.modules.FrozenCLIPEmbedder:
            model_embeddings = m.cond_stage_model.transformer.text_model.embeddings
            model_embeddings.token_embedding = EmbeddingsWithFixes(model_embeddings.token_embedding, self)
            m.cond_stage_model = sd_hijack_clip.FrozenCLIPEmbedderWithCustomWords(m.cond_stage_model, self)

        elif type(m.cond_stage_model) == ldm.modules.encoders.modules.FrozenOpenCLIPEmbedder:
            m.cond_stage_model.model.token_embedding = EmbeddingsWithFixes(m.cond_stage_model.model.token_embedding, self)
            m.cond_stage_model = sd_hijack_open_clip.FrozenOpenCLIPEmbedderWithCustomWords(m.cond_stage_model, self)

        apply_weighted_forward(m)
        if m.cond_stage_key == "edit":
            sd_hijack_unet.hijack_ddpm_edit()

        self.apply_optimizations()

        self.clip = m.cond_stage_model

        def flatten(el):
            flattened = [flatten(children) for children in el.children()]
            res = [el]
            for c in flattened:
                res += c
            return res

        self.layers = flatten(m)

        import modules.models.diffusion.ddpm_edit

        if isinstance(m, ldm.models.diffusion.ddpm.LatentDiffusion):
            sd_unet.original_forward = ldm_original_forward
        elif isinstance(m, modules.models.diffusion.ddpm_edit.LatentDiffusion):
            sd_unet.original_forward = ldm_original_forward
        elif isinstance(m, sgm.models.diffusion.DiffusionEngine):
            sd_unet.original_forward = sgm_original_forward
        else:
            sd_unet.original_forward = None