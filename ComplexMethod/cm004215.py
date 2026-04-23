def _init_weights(self, module):
        # important: this ported version of Idefics isn't meant for training from scratch - only
        # inference and fine-tuning - so the proper init weights code has been removed - the m4 code
        # base should be used for training from scratch and it contains the correct code.
        super()._init_weights(module)
        if isinstance(module, IdeficsVisionEmbeddings):
            init.normal_(module.class_embedding)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, IdeficsGatedCrossAttentionLayer):
            if self.config.alpha_initializer == "zeros":
                init.zeros_(module.alpha_cross_attn)
                init.zeros_(module.alpha_dense)
            elif self.config.alpha_initializer == "ones":
                init.ones_(module.alpha_cross_attn)
                init.ones_(module.alpha_dense)
            elif self.config.alpha_initializer in {"normal", "gaussian", "random"}:
                init.normal_(module.alpha_cross_attn, mean=0.0, std=self.config.alphas_initializer_range)
                init.normal_(module.alpha_dense, mean=0.0, std=self.config.alphas_initializer_range)
        elif isinstance(module, IdeficsPerceiverResampler):
            init.normal_(module.latents)
        elif isinstance(module, IdeficsEmbedding):
            inv_freq = 1.0 / (module.base ** (torch.arange(0, module.dim, 2) / module.dim))
            init.copy_(module.inv_freq, inv_freq)
            t = torch.arange(module.max_position_embeddings).type_as(inv_freq)
            freqs = torch.einsum("i,j->ij", t, inv_freq)
            # Different from paper, but it uses a different permutation in order to obtain the same calculation
            emb = torch.cat((freqs, freqs), dim=-1)
            init.copy_(module.cos_cached, emb.cos())
            init.copy_(module.sin_cached, emb.sin())