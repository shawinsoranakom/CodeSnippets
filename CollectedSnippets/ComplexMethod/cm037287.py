def load_model(self, target_model: nn.Module) -> None:
        target_attn_layer_names = set(
            get_layers_from_vllm_config(
                self.vllm_config,
                AttentionLayerBase,  # type: ignore[type-abstract]
            ).keys()
        )

        self.model = self._get_model()

        # Find draft layers (attention layers added by draft model)
        all_attn_layers = get_layers_from_vllm_config(
            self.vllm_config,
            AttentionLayerBase,  # type: ignore[type-abstract]
        )
        self._draft_attn_layer_names = (
            set(all_attn_layers.keys()) - target_attn_layer_names
        )

        if self.supports_mm_inputs:
            # Even if the target model is multimodal, we can also use
            # text-only draft models
            try:
                dummy_input_ids = torch.tensor([[1]], device=self.input_ids.device)
                self.model.embed_input_ids(dummy_input_ids, multimodal_embeddings=None)
            except (NotImplementedError, AttributeError, TypeError):
                logger.warning(
                    "Draft model does not support multimodal inputs, "
                    "falling back to text-only mode"
                )
                self.supports_mm_inputs = False

        if supports_multimodal(target_model):
            # handle multimodality
            assert hasattr(target_model, "config")
            if self.get_model_name(target_model) in [
                "Exaone4_5_ForConditionalGeneration",
                "GlmOcrForConditionalGeneration",
                "HunYuanVLForConditionalGeneration",
                "Qwen2_5_VLForConditionalGeneration",
                "Qwen3_5ForConditionalGeneration",
                "Qwen3_5MoeForConditionalGeneration",
                "Qwen3VLForConditionalGeneration",
                "Qwen3VLMoeForConditionalGeneration",
                "Gemma4ForConditionalGeneration",
            ]:
                self.model.config.image_token_index = target_model.config.image_token_id
            elif self.get_model_name(target_model) == "PixtralForConditionalGeneration":
                self.model.config.image_token_index = (
                    target_model.config.vision_config.image_token_id
                )
            elif self.get_model_name(target_model) == "KimiK25ForConditionalGeneration":
                self.model.config.image_token_index = (
                    target_model.config.media_placeholder_token_id
                )
            else:
                self.model.config.image_token_index = (
                    target_model.config.image_token_index
                )
            target_language_model = cast(
                SupportsMultiModal, target_model
            ).get_language_model()
        else:
            target_language_model = target_model

        self._maybe_share_embeddings(target_language_model)
        self._maybe_share_lm_head(target_language_model)

        if (
            self.parallel_drafting
            and self.pass_hidden_states_to_model
            and self.parallel_drafting_hidden_state_tensor is not None
        ):
            flat_mask = self.model.mask_hidden.view(-1)
            if self.eagle3_use_aux_hidden_state:
                # EAGLE3: mask_hidden stores all aux hidden states,
                # project through combine_hidden_states
                self.parallel_drafting_hidden_state_tensor.copy_(
                    self.model.combine_hidden_states(flat_mask)
                )
            else:
                self.parallel_drafting_hidden_state_tensor.copy_(flat_mask)