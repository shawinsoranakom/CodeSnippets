def embed_multimodal(self, **kwargs):
        pixel_values: torch.Tensor | None = kwargs.pop("pixel_values", None)
        image_embeds: torch.Tensor | None = kwargs.pop("image_embeds", None)
        # Model might use `image_patches` instead of `pixel_values`
        if pixel_values is None:
            pixel_values = kwargs.pop("image_patches", None)

        if image_embeds is not None:
            return image_embeds

        if pixel_values is None:
            return None

        num_image_patches = kwargs.pop("num_image_patches")
        kwargs.pop("token_type_ids", None)  # used only in `forward`
        kwargs.pop("mm_token_type_ids", None)  # used only in `model.get_rope_index`

        if pixel_values is not None:
            # ROCm: Force math SDP backend for vision encoder to avoid accuracy issues
            # with flash_sdp and mem_efficient_sdp
            if current_platform.is_rocm():
                # TODO: [ROCm] Fix accuracy issues with flash backend
                logger.debug(
                    "ROCm platform detected. Forcing math SDP backend "
                    "for vision encoder. Currently ROCm platform has "
                    "accuracy issues with `flash_sdp` and"
                    "`mem_efficient_sdp` backends. See issue: "
                    "https://github.com/vllm-project/vllm/issues/30167"
                )
                with torch.nn.attention.sdpa_kernel(
                    backends=[torch.nn.attention.SDPBackend.MATH]
                ):
                    vision_embeddings = self.model.get_image_features(
                        pixel_values, **kwargs
                    )
            else:
                vision_embeddings = self.model.get_image_features(
                    pixel_values, **kwargs
                )

            # Transformers `v5`, `self.get_image_features` returns a tuple
            # containing the features and optionally attentions/hidden_states
            # After v5 is settled, we can enable qwen3-vl with several outputs
            # from `self.get_image_features`
            if isinstance(vision_embeddings, tuple):
                vision_embeddings = vision_embeddings[0]
            elif isinstance(vision_embeddings, dict):
                vision_embeddings = vision_embeddings.pooler_output

            if isinstance(vision_embeddings, torch.Tensor):
                split_sizes = num_image_patches.flatten().tolist()
                total_patches = sum(split_sizes)

                # Flatten to 2D: [total_tokens, hidden_dim]
                if vision_embeddings.ndim == 3:
                    vision_embeddings = vision_embeddings.view(
                        -1, vision_embeddings.shape[-1]
                    )

                total_tokens = vision_embeddings.shape[0]
                if total_tokens == total_patches:
                    # Direct match: num_image_patches are actual token counts
                    # (e.g., Qwen2.5-VL style)
                    token_split_sizes = split_sizes
                elif total_patches > 0 and total_tokens % total_patches == 0:
                    # Uniform expansion: each patch expands to N tokens
                    # (e.g., Idefics3 style)
                    tokens_per_patch = total_tokens // total_patches
                    token_split_sizes = [s * tokens_per_patch for s in split_sizes]
                elif total_patches > 0:
                    # Mismatch (profiling with dummy data) - pad/truncate
                    if total_tokens == 0:
                        raise ValueError(
                            "Vision encoder returned empty embeddings. "
                            f"Expected {total_patches} patches from "
                            f"num_image_patches={split_sizes}"
                        )
                    if total_tokens < total_patches:
                        repeat_factor = (
                            total_patches + total_tokens - 1
                        ) // total_tokens
                        vision_embeddings = vision_embeddings.repeat(repeat_factor, 1)
                    vision_embeddings = vision_embeddings[:total_patches]
                    token_split_sizes = split_sizes
                else:
                    return []

                return list(torch.split(vision_embeddings, token_split_sizes, dim=0))

            return vision_embeddings
        else:
            logger.debug(
                "No pixel values or image embeddings provided for multimodal embedding."
            )
            return None