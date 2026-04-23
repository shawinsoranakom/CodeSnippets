def time_generate(
        self, config: BenchmarkConfig, warmup: bool
    ) -> tuple[float, list[float], str, GPURawMetrics | None]:
        # Prepare gpu monitoring if needed
        if config.gpu_monitoring and not warmup:
            gpu_monitor = GPUMonitor(logger=self.logger)
            gpu_monitor.start()
        else:
            gpu_monitor = None

        # Generate and time
        if config.continuous_batching:
            inputs = self.inputs["input_ids"].tolist()
            wall_time_0 = time.perf_counter()
            outputs = self.model.generate_batch(inputs, allow_block_sharing=False, record_timestamps=True)
        else:
            streamer = BenchmarkStreamer()
            wall_time_0 = time.perf_counter()
            outputs = self.model.generate(**self.inputs, streamer=streamer)

        wall_time_1 = time.perf_counter()
        gpu_metrics = gpu_monitor.stop_and_collect() if gpu_monitor is not None else None

        # Retrieve timestamps and results in a way that allows similar post-processing
        input_tokens = self.inputs["input_ids"].size(-1)
        if config.continuous_batching:
            timestamps = [output.timestamps[:] for output in outputs.values()]
            results = torch.tensor([output.generated_tokens[:] for output in outputs.values()])
        else:
            timestamps = [streamer.timestamps[1:]]  # skip the first timestamp because it's the input tokens
            results = outputs[:, input_tokens:]
        outputs = None
        flush_memory(flush_compile=False)

        # Check if generation had the right number of tokens
        if results.size(-1) != config.num_tokens_to_generate:
            raise RuntimeError(f"Generated {results.size(-1)} tokens, expected {config.num_tokens_to_generate}")

        # Decode outputs
        decoded_output = self.tokenizer.decode(results[0], skip_special_tokens=True)
        shape_and_decoded_output = f"{tuple(results.shape)} | {decoded_output}"

        # Compute metrics
        e2e_latency = wall_time_1 - wall_time_0
        timestamps = torch.tensor(timestamps).sub(wall_time_0).tolist()
        self.logger.info(
            f"Time generate done in {e2e_latency:.2f} seconds. Memory usage: {self.torch_accelerator_module.memory_allocated() / 1024**2:.2f} MB"
        )
        return e2e_latency, timestamps, shape_and_decoded_output, gpu_metrics