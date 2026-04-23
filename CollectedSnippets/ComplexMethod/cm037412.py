def load_model(self, load_dummy_weights: bool = False, *args, **kwargs) -> None:
        time_before_load = time.perf_counter()
        if load_dummy_weights:
            self.load_config.load_format = "dummy"
        self.eplb.prepare_load()
        eplb_models_added = False
        with DeviceMemoryProfiler() as m:
            model_loader = get_model_loader(self.vllm_config.load_config)
            logger.info("Loading model from scratch...")

            self.model = model_loader.load_model(
                vllm_config=self.vllm_config, model_config=self.vllm_config.model_config
            )
            if self.lora_config:
                self.model = self.load_lora_model(
                    self.model, self.vllm_config, self.device
                )

            if self.use_aux_hidden_state_outputs:
                assert self.speculative_config is not None
                set_eagle3_aux_hidden_state_layers(self.model, self.speculative_config)
            if self.speculator is not None:
                self.speculator.load_model(self.model)
                eplb_models_added = self.eplb.maybe_register_speculator(
                    self.speculator, self.speculative_config, load_dummy_weights
                )
        time_after_load = time.perf_counter()

        self.model_memory_usage = m.consumed_memory
        logger.info(
            "Model loading took %s GiB and %.6f seconds",
            format_gib(m.consumed_memory),
            time_after_load - time_before_load,
        )

        if not load_dummy_weights:
            prepare_communication_buffer_for_model(self.model)
            if self.speculator is not None:
                prepare_communication_buffer_for_model(self.speculator.model)

        # Initialize the components that require the model.
        self.model_state = init_model_state(
            self.vllm_config, self.model, self.encoder_cache, self.device
        )
        if self.is_pooling_model and self.is_last_pp_rank:
            self.pooling_runner = PoolingRunner(self.model)
        eplb_models_added |= self.eplb.maybe_register_model(
            self.model,
            self.model_config,
            load_dummy_weights,
        )
        self.eplb.maybe_start_async_loop(eplb_models_added)

        if not self.is_first_pp_rank:
            # For non-first PP ranks, create intermediate tensors sized
            # for the max capture size so they can be sliced per batch.
            # Save as persistent member so runtime can copy received data
            # into the same addresses that the CUDA graphs captured.
            self.intermediate_tensors = self.model.make_empty_intermediate_tensors(
                batch_size=self.max_num_tokens,
                dtype=self.model_config.dtype,
                device=self.device,
            )