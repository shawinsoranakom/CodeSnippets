def load_model(self, load_dummy_weights: bool = False) -> None:
        """
        Args:
            load_dummy_weights: load dummy weights instead of real weights.
        """
        logger.info_once(
            "Starting to load model %s...",
            self.model_config.model,
            scope="global",
        )

        if self.parallel_config.enable_eplb:
            self.eplb_state = EplbState(self.parallel_config, self.device)
            eplb_models = 0

        try:
            with DeviceMemoryProfiler() as m:
                time_before_load = time.perf_counter()
                if load_dummy_weights:
                    self.load_config.load_format = "dummy"
                model_loader = get_model_loader(self.load_config)
                self.model = model_loader.load_model(
                    vllm_config=self.vllm_config, model_config=self.model_config
                )
                if self.lora_config:
                    self.model = self.load_lora_model(
                        self.model, self.vllm_config, self.device
                    )
                if hasattr(self, "drafter"):
                    logger.info_once("Loading drafter model...")
                    self.drafter.load_model(self.model)
                    if (
                        hasattr(self.drafter, "model")
                        and is_mixture_of_experts(self.drafter.model)
                        and self.parallel_config.enable_eplb
                    ):
                        assert not self.parallel_config.enable_elastic_ep, (
                            "Elastic EP is not supported with drafter model."
                        )
                        spec_config = self.vllm_config.speculative_config
                        assert spec_config is not None
                        assert spec_config.draft_model_config is not None
                        logger.info_once(
                            "EPLB is enabled for drafter model %s.",
                            spec_config.draft_model_config.model,
                        )
                        if self.eplb_state is None:
                            self.eplb_state = EplbState(
                                self.parallel_config, self.device
                            )
                        self.eplb_state.add_model(
                            self.drafter.model,
                            spec_config.draft_model_config,
                        )
                        eplb_models += 1

                if self.use_aux_hidden_state_outputs:
                    if not supports_eagle3(self.get_model()):
                        raise RuntimeError(
                            "Model does not support EAGLE3 interface but "
                            "aux_hidden_state_outputs was requested"
                        )

                    # Try to get auxiliary layers from speculative config,
                    # otherwise use model's default layers
                    aux_layers = self._get_eagle3_aux_layers_from_config()
                    if aux_layers:
                        logger.info(
                            "Using auxiliary layers from speculative config: %s",
                            aux_layers,
                        )
                    else:
                        aux_layers = (
                            self.model.get_eagle3_default_aux_hidden_state_layers()
                        )

                    self.model.set_aux_hidden_state_layers(aux_layers)

                if (
                    is_mixture_of_experts(self.model)
                    and self.parallel_config.enable_eplb
                    and not load_dummy_weights
                ):
                    logger.info_once(
                        "EPLB is enabled for model %s.",
                        self.model_config.model,
                    )
                    assert self.eplb_state is not None
                    self.eplb_state.add_model(
                        self.model,
                        self.model_config,
                    )
                    eplb_models += 1

                time_after_load = time.perf_counter()
            self.model_memory_usage = m.consumed_memory
        except torch.cuda.OutOfMemoryError as e:
            msg = (
                "Failed to load model - not enough GPU memory. "
                "Try lowering --gpu-memory-utilization to free memory for weights, "
                "increasing --tensor-parallel-size, or using --quantization. "
                "See https://docs.vllm.ai/en/latest/configuration/conserving_memory/ "
                "for more tips."
            )
            combined_msg = f"{msg} (original error: {e})"
            logger.error(combined_msg)
            raise e
        logger.info_once(
            "Model loading took %s GiB memory and %.6f seconds",
            format_gib(self.model_memory_usage),
            time_after_load - time_before_load,
        )
        if not load_dummy_weights:
            prepare_communication_buffer_for_model(self.model)
            if (drafter := getattr(self, "drafter", None)) and (
                drafter_model := getattr(drafter, "model", None)
            ):
                prepare_communication_buffer_for_model(drafter_model)
        mm_config = self.model_config.multimodal_config
        self.is_multimodal_pruning_enabled = (
            supports_multimodal_pruning(self.get_model())
            and mm_config is not None
            and mm_config.is_multimodal_pruning_enabled()
        )
        self.requires_sequential_video_encoding = hasattr(
            self.get_model(), "requires_sequential_video_encoding"
        )  # Temporary hack for dynamic res video w/o support for bs>1 yet

        if (
            is_mixture_of_experts(self.model)
            and self.parallel_config.enable_eplb
            and not load_dummy_weights
            and self.eplb_state is not None
            and self.eplb_state.is_async
        ):
            self.eplb_state.start_async_loop()

        if (
            self.vllm_config.compilation_config.mode
            == CompilationMode.STOCK_TORCH_COMPILE
        ):
            from vllm.env_override import _apply_constrain_to_fx_strides_patch

            _apply_constrain_to_fx_strides_patch()
            backend = self.vllm_config.compilation_config.init_backend(self.vllm_config)
            compilation_counter.stock_torch_compile_count += 1
            self.model.compile(fullgraph=True, backend=backend)
            return
        # for other compilation modes, cudagraph behavior is controlled by
        # CudagraphWrapper and CudagraphDispatcher of vllm.

        # wrap the model with full cudagraph wrapper if needed.
        cudagraph_mode = self.compilation_config.cudagraph_mode
        assert cudagraph_mode is not None
        if (
            cudagraph_mode.has_full_cudagraphs()
            and not self.parallel_config.use_ubatching
        ):
            self.model = CUDAGraphWrapper(
                self.model, self.vllm_config, runtime_mode=CUDAGraphMode.FULL
            )
        elif self.parallel_config.use_ubatching:
            if cudagraph_mode.has_full_cudagraphs():
                self.model = UBatchWrapper(
                    self.model, self.vllm_config, CUDAGraphMode.FULL, self.device
                )
            else:
                self.model = UBatchWrapper(
                    self.model, self.vllm_config, CUDAGraphMode.NONE, self.device
                )

        get_offloader().post_init()