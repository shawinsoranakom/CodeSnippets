def profile_run(self) -> None:
        # Profile with multimodal encoder & encoder cache.
        if self.supports_mm_inputs:
            mm_config = self.model_config.multimodal_config
            if mm_config is not None and mm_config.skip_mm_profiling:
                logger.info(
                    "Skipping memory profiling for multimodal encoder and "
                    "encoder cache."
                )
            else:
                mm_budget = self.mm_budget
                assert mm_budget is not None

                if (encoder_budget := mm_budget.get_encoder_budget()) > 0:
                    if not mm_budget.mm_max_toks_per_item:
                        # All modality limits are 0 — embedding-only mode.
                        # Budget is non-zero for embedding storage, but
                        # there's no encoder to profile.
                        logger.info(
                            "Skipping encoder profiling for embedding-only "
                            "mode (all modality limits=0 with "
                            "enable_mm_embeds=True).",
                        )
                    else:
                        # NOTE: Currently model is profiled with a single
                        # non-text modality with the max possible input
                        # tokens even when it supports multiple.
                        dummy_modality = mm_budget.get_modality_with_max_tokens()
                        max_mm_items_per_batch = mm_budget.mm_max_items_per_batch[
                            dummy_modality
                        ]

                        logger.info_once(
                            "Encoder cache will be initialized with a "
                            "budget of %s tokens, and profiled with "
                            "%s %s items of the maximum feature size.",
                            encoder_budget,
                            max_mm_items_per_batch,
                            dummy_modality,
                        )

                        # Create dummy batch of multimodal inputs.
                        batched_dummy_mm_inputs = self._get_mm_dummy_batch(
                            dummy_modality,
                            max_mm_items_per_batch,
                        )

                        # Run multimodal encoder.
                        dummy_encoder_outputs = self.model.embed_multimodal(
                            **batched_dummy_mm_inputs
                        )

                        sanity_check_mm_encoder_outputs(
                            dummy_encoder_outputs,
                            expected_num_items=max_mm_items_per_batch,
                        )
                        for i, output in enumerate(dummy_encoder_outputs):
                            self.encoder_cache[f"tmp_{i}"] = output

        # Add `is_profile` here to pre-allocate communication buffers
        hidden_states, last_hidden_states = self._dummy_run(
            self.max_num_tokens, is_profile=True
        )
        if get_pp_group().is_last_rank:
            if self.is_pooling_model:
                output = self._dummy_pooler_run(hidden_states)
            else:
                output = self._dummy_sampler_run(last_hidden_states)
        else:
            output = None
        self._sync_device()
        del hidden_states, output
        self.encoder_cache.clear()
        gc.collect()