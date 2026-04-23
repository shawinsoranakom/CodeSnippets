def embed_input_ids(
        self,
        input_ids: torch.Tensor,
        multimodal_embeddings: MultiModalEmbeddings | None = None,
        *,
        is_multimodal: torch.Tensor | None = None,
    ) -> torch.Tensor:
        inputs_embeds = self._embed_text_input_ids(
            input_ids,
            self.language_model.embed_input_ids,
            is_multimodal=is_multimodal,
        )

        if multimodal_embeddings is None or len(multimodal_embeddings) == 0:
            return inputs_embeds

        # Detect interleaved audio-in-video early, since it affects
        # both the deepstack path and the final embedding merge.
        video_token_id = self.config.video_token_id
        audio_token_id = self.config.audio_token_id
        input_ids_cpu = input_ids.cpu()
        is_video = is_multimodal & (input_ids_cpu == video_token_id)
        is_audio = is_multimodal & (input_ids_cpu == audio_token_id)
        num_video = is_video.sum().item()
        num_audio = is_audio.sum().item()

        is_interleaved = check_interleaved_audio_video(
            is_video, is_audio, num_video, num_audio
        )

        deepstack_input_embeds = None
        # split the feat dim to obtain multi-scale visual feature
        has_vision_embeddings = [
            embeddings.shape[-1] != self.config.text_config.hidden_size
            for embeddings in multimodal_embeddings
        ]
        if self.visual.deepstack_visual_indexes is not None and any(
            has_vision_embeddings
        ):
            multiscale_len = len(self.visual.deepstack_visual_indexes)
            multimodal_embeddings_multiscale = []

            if is_interleaved:
                # Use input_ids-based mask for correct vision positions
                # when audio and video tokens are interleaved.
                is_vision = is_video.clone()
            else:
                is_vision = torch.zeros_like(is_multimodal)
                mm_positions = torch.nonzero(is_multimodal, as_tuple=True)[0]
                mm_position_idx = 0

            for index, embeddings in enumerate(multimodal_embeddings):
                num_tokens = embeddings.shape[0]

                # Vision embeddings
                if embeddings.shape[-1] != self.config.text_config.hidden_size:
                    visual_dim = embeddings.shape[-1] // (multiscale_len + 1)
                    multi_dim = visual_dim * multiscale_len
                    embeddings_main, embeddings_multiscale = torch.split(
                        embeddings, [visual_dim, multi_dim], dim=-1
                    )
                    multimodal_embeddings[index] = embeddings_main
                    multimodal_embeddings_multiscale.append(embeddings_multiscale)
                    if not is_interleaved:
                        current_positions = mm_positions[
                            mm_position_idx : mm_position_idx + num_tokens
                        ]
                        is_vision[current_positions] = True

                # Audio embeddings
                else:
                    if not is_interleaved:
                        current_positions = mm_positions[
                            mm_position_idx : mm_position_idx + num_tokens
                        ]
                        is_vision[current_positions] = False

                if not is_interleaved:
                    mm_position_idx += num_tokens

            deepstack_input_embeds = inputs_embeds.new_zeros(
                inputs_embeds.size(0), multiscale_len * inputs_embeds.size(1)
            )
            deepstack_input_embeds = _merge_multimodal_embeddings(
                inputs_embeds=deepstack_input_embeds,
                multimodal_embeddings=multimodal_embeddings_multiscale,
                is_multimodal=is_vision,
            )
            deepstack_input_embeds = (
                deepstack_input_embeds.view(
                    inputs_embeds.shape[0], multiscale_len, visual_dim
                )
                .permute(1, 0, 2)
                .contiguous()
            )
            self._set_deepstack_input_embeds(deepstack_input_embeds)

        if is_interleaved:
            return merge_interleaved_embeddings(
                inputs_embeds,
                multimodal_embeddings,
                is_video,
                is_audio,
                is_multimodal,
                num_video,
                num_audio,
            )

        # Default: standard merge (no interleaving), same as parent class.
        # multimodal_embeddings may have been updated above (deepstack
        # main-scale). Use super() to stay consistent with the parent
        # implementation and avoid issues seen in Qwen2.5-Omni (#34506).
        return super().embed_input_ids(
            input_ids,
            multimodal_embeddings=multimodal_embeddings,
            is_multimodal=is_multimodal,
        )