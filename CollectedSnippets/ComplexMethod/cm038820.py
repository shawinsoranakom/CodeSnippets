def _maybe_init_mm(
        self,
        vllm_config: VllmConfig,
        max_num_batched_tokens: int,
    ) -> None:
        mm_registry = MULTIMODAL_REGISTRY

        self.supports_tower_connector_lora = False
        self.mm_mapping: MultiModelKeys = self.model.get_mm_mapping()

        # Only one language model can be included in the model.
        assert len(self.mm_mapping.language_model) == 1

        # Language model punica wrapper
        llm_punica_wrapper = get_punica_wrapper(
            max_num_batched_tokens,
            max_batches=self.max_num_seqs,
            device=self.device,
            lora_config=self.lora_config,
        )

        lm_prefix = self.mm_mapping.language_model[0]
        self.punica_wrapper_mapping[lm_prefix] = llm_punica_wrapper

        # First, determine if the model supports tower connector LoRA.
        self.supports_tower_connector_lora = self.supports_mm and hasattr(
            self.model, "get_num_mm_encoder_tokens"
        )

        # Then, handle the case where the feature is disabled in the config.
        if not self.lora_config.enable_tower_connector_lora:
            if self.supports_tower_connector_lora:
                logger.info(
                    "%s supports adding LoRA to the tower modules. If needed, "
                    "please set `enable_tower_connector_lora=True`.",
                    self.model.__class__.__name__,
                )
            self.supports_tower_connector_lora = False
            return

        # After this point, the feature is enabled in the config.
        # Now check if it's supported by the model.
        if not self.supports_tower_connector_lora:
            # Enabled but not supported: log warning and return.
            logger.warning(
                "LoRA with tower connector is enabled, but the model %s "
                "does not support it. This will be ignored.",
                self.model.__class__.__name__,
            )
            return

        # Check if initialize the language model only.
        if (
            vllm_config.model_config.multimodal_config
            and vllm_config.model_config.multimodal_config.language_model_only
        ):
            logger.warning(
                "Disabling `enable_tower_connector_lora` because the multimodal "
                "model is configured to initialize the language model only."
            )
            self.supports_tower_connector_lora = False
            return

        logger.warning(
            "LoRA for the tower and connector of multimodal models is "
            "experimental and may contain bugs. Please report any related issues on "
            "GitHub if you encounter them."
        )

        mm_budget = MultiModalBudget(vllm_config, mm_registry)
        limit_per_prompt = max(mm_budget.mm_max_items_per_prompt.values())
        num_encoder_tokens = self.model.get_num_mm_encoder_tokens(
            mm_budget.get_encoder_budget()
        )

        # Tower wrappers
        tower_punica_wrapper = get_punica_wrapper(
            num_encoder_tokens,
            max_batches=self.max_num_seqs * limit_per_prompt,
            device=self.device,
            lora_config=self.lora_config,
        )
        for prefix in self.mm_mapping.tower_model:
            self.punica_wrapper_mapping[prefix] = tower_punica_wrapper

        # Use wrapper for connector if present.
        if self.mm_mapping.connector:
            if hasattr(self.model, "get_num_mm_connector_tokens"):
                connector_tokens = self.model.get_num_mm_connector_tokens(
                    num_encoder_tokens
                )
                connector_punica_wrapper = get_punica_wrapper(
                    connector_tokens,
                    max_batches=self.max_num_seqs * limit_per_prompt,
                    device=self.device,
                    lora_config=self.lora_config,
                )
                for prefix in self.mm_mapping.connector:
                    self.punica_wrapper_mapping[prefix] = connector_punica_wrapper
            else:
                logger.warning_once(
                    "Connector LoRA support disabled: model does not implement "
                    "get_num_mm_connector_tokens(). This method is required to "
                    "determine the connector's token budget for LoRA operations."
                )