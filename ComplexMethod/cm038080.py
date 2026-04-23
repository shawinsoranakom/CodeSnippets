def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]) -> set[str]:
        """Load weights from checkpoint."""
        # Skip generation-related weights since we only support text2text and image2text
        # Filter out all image generation components:
        # - 'moe_gen': MoE generation weights
        # - 'latent_pos_embed': Latent position embeddings for VAE
        # - 'llm2vae', 'vae2llm': LLM-VAE projections
        # - 'time_embedder': Timestep embeddings for diffusion
        # - VAE encoder/decoder: Use specific prefixes to avoid matching vision encoder
        generation_keywords = [
            "moe_gen",
            "latent_pos_embed",
            "llm2vae",
            "vae2llm",
            "time_embedder",
        ]
        vae_prefixes = [
            "decoder.",
            "encoder.",
        ]  # VAE encoder/decoder, not vision encoder
        filtered_weights = []
        for name, tensor in weights:
            # Skip generation-related keywords
            if any(skip in name for skip in generation_keywords):
                continue
            if any(name.startswith(prefix) for prefix in vae_prefixes):
                continue

            if "patch_embedding.weight" in name and tensor.ndim == 2:
                out_channels = tensor.shape[0]
                in_features = tensor.shape[1]
                patch_size = self.config.vit_config.patch_size
                in_channels = self.config.vit_config.num_channels
                if in_features == in_channels * patch_size * patch_size:
                    tensor = tensor.reshape(
                        out_channels, patch_size, patch_size, in_channels
                    )
                    tensor = tensor.permute(0, 3, 1, 2).contiguous()

            filtered_weights.append((name, tensor))

        # Skip vit_pos_embed.pos_embed as it's handled by PositionEmbedding module
        loader = AutoWeightsLoader(self, skip_prefixes=["vit_pos_embed.pos_embed"])
        return loader.load_weights(filtered_weights, mapper=self.hf_to_vllm_mapper)