def run_performance_test_non_alternate(
        self, name, model, example_inputs, optimize_ctx, experiment, tag=None
    ):
        "Run performance test in non-alternately."
        if experiment.func is not latency_experiment:
            raise AssertionError(
                f"Must run with latency_experiment, got {experiment.func}"
            )

        def warmup(fn, model, example_inputs, mode, niters=10):
            gc.collect()
            peak_mem = 0
            start_stats = get_dynamo_stats()
            try:
                if current_device == "cuda":
                    torch.cuda.reset_peak_memory_stats()
                    empty_gpu_cache(current_device)
                elif current_device == "hpu":
                    torch.hpu.reset_peak_memory_stats()
                t0 = time.perf_counter()
                for _ in range(niters):
                    fn(model, example_inputs)
                t1 = time.perf_counter()
                latency = t1 - t0
                if current_device == "cuda":
                    peak_mem = get_peak_memory()
                elif current_device == "hpu":
                    peak_mem = torch.hpu.max_memory_allocated() / 10**9
                elif current_device == "cpu":
                    total = psutil.virtual_memory().total
                    percentage = psutil.Process(os.getpid()).memory_percent()
                    peak_mem = percentage * total / 10**9
            except Exception:
                log.exception("Backend %s failed in warmup()", mode)
                write_csv_when_exception(
                    self.args, current_name, "warmup_failed", current_device
                )
                output_signpost({}, self.args, self.suite_name, error="warmup_failed")
                return sys.exit(-1)
            dynamo_stats = get_dynamo_stats()
            dynamo_stats.subtract(start_stats)
            return latency, peak_mem, dynamo_stats

        # Cast the model to float16/float32 as necessary
        model, example_inputs = self.maybe_cast(model, example_inputs)

        # Use distributed wrapping as necessary
        model = self.deepcopy_and_maybe_parallelize(model)

        if not hasattr(model, name):
            model.name = name
        self.init_optimizer(name, current_device, model.parameters())

        # The self.autocast context is needed for the model we export with aot_compile,
        # similar to what we do in the check_accuracy function
        ctx = (
            self.autocast(**self.autocast_arg)
            if self.args.export_aot_inductor
            else contextlib.nullcontext()
        )

        with self.pick_grad(name, self.args.training), ctx:
            ok, total = Stats.reset_counters()
            experiment_kwargs = {}
            if tag is not None:
                experiment_kwargs["tag"] = tag
            results = []

            with maybe_snapshot_memory(
                self.args.snapshot_memory, f"eager_{self.args.only}"
            ):
                eager_latency, eager_peak_mem, _ = warmup(
                    self.model_iter_fn, model, example_inputs, "eager"
                )
                if self.args.use_warm_peak_memory:
                    _, eager_peak_mem, _ = warmup(
                        self.model_iter_fn, model, example_inputs, "eager", niters=1
                    )

            baseline_timings = experiment(
                self.model_iter_fn,
                model,
                example_inputs,
                mark="expected",
                **experiment_kwargs,
            )

            # reset dynamo
            torch._dynamo.reset()

            if self.args.export_aot_inductor:
                optimized_model_iter_fn = optimize_ctx
            else:
                optimized_model_iter_fn = optimize_ctx(self.model_iter_fn)

            with maybe_snapshot_memory(
                self.args.snapshot_memory, f"compiled_{self.args.only}"
            ):
                dynamo_latency, dynamo_peak_mem, dynamo_stats = warmup(
                    optimized_model_iter_fn, model, example_inputs, "dynamo"
                )
                if self.args.use_warm_peak_memory:
                    _, dynamo_peak_mem, _ = warmup(
                        optimized_model_iter_fn,
                        model,
                        example_inputs,
                        "dynamo",
                        niters=1,
                    )
                # If we use warm peak memory, the AOT model loading transient memory
                # won't be present on the warm measurement.  We only have to account for
                # it when using cold memory.
                elif self.args.export_aot_inductor:
                    dynamo_peak_mem -= AOTInductorModelCache.get_excess_memory(model)

            if self.args.profile_dynamo_cache_lookup:
                with torch.profiler.profile(
                    activities=[torch.profiler.ProfilerActivity.CPU]
                ) as prof:
                    warmup(optimized_model_iter_fn, model, example_inputs, "dynamo")

                events = list(
                    filter(
                        lambda event: "TorchDynamo Cache Lookup" in event.key,
                        prof.key_averages(),
                    )
                )
                dynamo_cache_lookup_latency = events[0].self_cpu_time_total

            compilation_time = dynamo_latency - eager_latency
            compression_ratio = (
                eager_peak_mem / dynamo_peak_mem if dynamo_peak_mem else 0.0
            )
            if self.args.print_memory:
                print(
                    f"memory: eager: {eager_peak_mem:.2f} GB, "
                    f"dynamo: {dynamo_peak_mem:.2f} GB, "
                    f"ratio: {compression_ratio:.2f}"
                )

            if self.args.print_compilation_time:
                print(f"Compilation time: {compilation_time:.2f}")

            if experiment.func is speedup_experiment:
                experiment_kwargs["compilation_latency"] = compilation_time
                experiment_kwargs["compression_ratio"] = compression_ratio
                experiment_kwargs["eager_peak_mem"] = eager_peak_mem
                experiment_kwargs["dynamo_peak_mem"] = dynamo_peak_mem
                experiment_kwargs["dynamo_stats"] = dynamo_stats
                if self.args.profile_dynamo_cache_lookup:
                    experiment_kwargs["cache_lookup_latency"] = (
                        dynamo_cache_lookup_latency
                    )

            backend_timings = experiment(
                self.model_iter_fn,
                model,
                example_inputs,
                mark="expected",
                **experiment_kwargs,
            )
            timings = np.stack((baseline_timings, backend_timings), axis=1)
            result_summary = latency_experiment_summary(
                self.suite_name, self.args, model, timings, **experiment_kwargs
            )
            results.append(result_summary)
            return " ".join(map(str, results))