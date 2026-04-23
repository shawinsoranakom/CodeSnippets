def generate_batch(
        self,
        inputs: list[list[int]],
        generation_config: GenerationConfig | None = None,
        continuous_batching_config: ContinuousBatchingConfig | None = None,
        record_timestamps: bool = False,
        progress_bar: bool = True,
        persistent_manager: bool = False,
        warmup: bool = True,
        **kwargs,
    ) -> dict[str, GenerationOutput]:
        """Generate sequences for a batch of prompts using continuous batching.

        Args:
            inputs: List of input token sequences (prompts)
            generation_config: Optional generation configuration
            continuous_batching_config: Optional continuous batching configuration
            record_timestamps: If set to true, the requests will have a timestamp for each token generated
            progress_bar: If set to true, a progress bar will be displayed
            persistent_manager: whether to persist the manager after the generation is finished. Default is False.
            warmup: whether to pre-capture CUDA graphs before processing requests. Default is True.
            **kwargs: Additional generation parameters. Only max_new_tokens is used, but other deprecated arguments
                are extracted and passed to the continuous_batching_config object.
        Returns:
            `dict[str, GenerationOutput]`: a dictionary of request ids to GenerationOutput objects
        """
        # If no input are provided, return an empty dictionary
        if not inputs:
            return {}

        # If the logger level is less than DEBUG, disable the progress bar
        if logger.getEffectiveLevel() <= logging.DEBUG:
            logger.warning("Progress bar is disabled when logger level is less than DEBUG")
            progress_bar = False

        # Extract deprecated arguments from regular kwargs (deprecated in v5.3). These args are now expected in the
        # continuous_batching_config object.
        deprecated_kwargs = {}
        deprecated_keys = [
            "q_padding_interval_size",
            "kv_padding_interval_size",
            "allow_block_sharing",
            "use_async_batching",
            "max_cached_graphs",
            "max_queue_size",
        ]
        for depr_key in deprecated_keys:
            if depr_key in kwargs:
                deprecated_kwargs[depr_key] = kwargs.pop(depr_key)
        # Extract max_new_tokens from kwargs because it's the only expected kwarg
        max_new_tokens = kwargs.pop("max_new_tokens", None)

        # Compute the total number of requests
        gen_cfg = self.generation_config if generation_config is None else generation_config
        num_return_sequences = gen_cfg.num_return_sequences if gen_cfg.num_return_sequences is not None else 1
        num_requests = len(inputs) * num_return_sequences

        # Prepare context managers for the main loop
        manager_cm = self.continuous_batching_context_manager(
            generation_config=generation_config,
            continuous_batching_config=continuous_batching_config,
            block=True,
            timeout=5,
            persistent_manager=persistent_manager,
            warmup_requests=len(inputs) if warmup else None,
            **deprecated_kwargs,
        )
        logging_cm = logging_redirect_tqdm([logger])
        pbar_cm = tqdm(
            total=num_requests,
            disable=(not progress_bar),
            desc=f"Solving {num_requests} requests",
            unit="request",
        )

        # Main loop
        results = {}
        finished_count = 0
        with manager_cm as manager, logging_cm, pbar_cm as pbar:
            try:
                manager.add_requests(inputs=inputs, max_new_tokens=max_new_tokens, record_timestamps=record_timestamps)
                while finished_count < num_requests:
                    result = manager.get_result(timeout=1)
                    if result:
                        req_id = result.request_id
                        if result.is_finished():
                            results[req_id] = result
                            finished_count += 1
                            pbar.update(1)
                    elif not manager.is_running():
                        logger.error("Generation thread terminated unexpectedly.")
                        # This helps get some information in stdout
                        print("Returning results of generate_batch despite unexpected termination.")
                        break

            except Exception as e:
                logger.error(f"Error during batch generation: {e}", exc_info=True)

        # Re-order requests to match the order of the inputs
        reordered_results = {}
        for i in range(len(inputs)):
            # We cannot guarantee generation success for all requests, so check if the request is in the results
            result = results.get(f"req_{i}")
            if result is not None:
                reordered_results[f"req_{i}"] = result
            else:
                logger.error(f"Request req_{i} not found in results.")
        return reordered_results