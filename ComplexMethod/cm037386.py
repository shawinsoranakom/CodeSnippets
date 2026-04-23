def capture_model(self) -> int:
        if self.compilation_config.cudagraph_mode == CUDAGraphMode.NONE:
            logger.warning(
                "Skipping CUDA graph capture. To turn on CUDA graph capture, "
                "ensure `cudagraph_mode` was not manually set to `NONE`"
            )
            return 0

        # Initialize encoder CUDA graph manager if enabled.
        # Use get_model() to unwrap CUDAGraphWrapper/UBatchWrapper,
        # because @runtime_checkable Protocol isinstance() checks do not
        # work through __getattr__ forwarding.
        if (
            self.compilation_config.cudagraph_mm_encoder
            and self.supports_mm_inputs
            and self.encoder_cudagraph_manager is None
        ):
            from vllm.model_executor.models.interfaces import (
                SupportsEncoderCudaGraph,
                supports_encoder_cudagraph,
            )
            from vllm.v1.worker.encoder_cudagraph import (
                EncoderCudaGraphManager,
            )

            raw_model = self.get_model()
            if supports_encoder_cudagraph(raw_model):
                self.encoder_cudagraph_manager = EncoderCudaGraphManager(
                    vllm_config=self.vllm_config,
                    device=self.device,
                    dtype=self.dtype,
                    model=cast(SupportsEncoderCudaGraph, raw_model),
                )
                logger.info("Initialized EncoderCudaGraphManager for vision encoder")

        compilation_counter.num_gpu_runner_capture_triggers += 1

        start_time = time.perf_counter()

        # Trigger CUDA graph capture for specific shapes.
        # Capture the large shapes first so that the smaller shapes
        # can reuse the memory pool allocated for the large shapes.
        set_cudagraph_capturing_enabled(True)
        with self._freeze_gc(), graph_capture(device=self.device):
            torch.accelerator.synchronize()
            torch.accelerator.empty_cache()
            start_free_gpu_memory = torch.cuda.mem_get_info()[0]

            for (
                runtime_mode,
                batch_descs,
            ) in self.cudagraph_dispatcher.get_capture_descs():
                self._capture_cudagraphs(
                    batch_descriptors=batch_descs,
                    cudagraph_runtime_mode=runtime_mode,
                )
                torch.accelerator.synchronize()

            # Capture encoder CUDA graphs if enabled
            if self.encoder_cudagraph_manager is not None:
                self.encoder_cudagraph_manager.capture()

            torch.accelerator.synchronize()
            end_free_gpu_memory = torch.cuda.mem_get_info()[0]

        # Disable cudagraph capturing globally, so any unexpected cudagraph
        # capturing will be detected and raise an error after here.
        # Note: We don't put it into graph_capture context manager because
        # we may do lazy capturing in future that still allows capturing
        # after here.
        set_cudagraph_capturing_enabled(False)

        torch.accelerator.synchronize()
        torch.accelerator.empty_cache()

        # Lock workspace to prevent resizing during execution.
        # Max workspace sizes should have been captured during warmup/profiling.
        lock_workspace()

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        cuda_graph_size = start_free_gpu_memory - end_free_gpu_memory
        # This usually takes 5~20 seconds.
        logger.info_once(
            "Graph capturing finished in %.0f secs, took %.2f GiB",
            elapsed_time,
            cuda_graph_size / (1 << 30),
        )
        return cuda_graph_size