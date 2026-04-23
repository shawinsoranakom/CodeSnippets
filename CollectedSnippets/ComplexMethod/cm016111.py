def run_performance_test(
        self,
        name,
        model,
        example_inputs,
        optimize_ctx,
        experiment,
        tag=None,
        batch_size=None,
    ):
        niters = 5
        if getattr(self, "hf_llm", False):
            # If we're benchmarking an llm, we want to use the generate function
            self.model_iter_fn = self.generate
            niters = 1

        if self.args.xla:
            with self.pick_grad(name, self.args.training):
                return experiment(
                    self.model_iter_fn, *self.maybe_cast(model, example_inputs)
                )

        def warmup(fn, model, example_inputs, mode, niters=5):
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
            experiment_kwargs["batch_size"] = batch_size
            if tag is not None:
                experiment_kwargs["tag"] = tag
            results = []
            with maybe_snapshot_memory(
                self.args.snapshot_memory, f"eager_{self.args.only}"
            ):
                with torch.compiler.set_stance("force_eager"):
                    eager_latency, eager_peak_mem, _ = warmup(
                        self.model_iter_fn,
                        copy.deepcopy(model),
                        example_inputs,
                        "eager",
                        niters=niters,
                    )
                    if self.args.use_warm_peak_memory:
                        _, eager_peak_mem, _ = warmup(
                            self.model_iter_fn,
                            copy.deepcopy(model),
                            example_inputs,
                            "eager",
                            niters=1,
                        )

            if (
                self.args.export_aot_inductor
                or self.args.export_nativert
                or self.args.torchscript_jit_trace
                or self.args.aot_precompile
            ):
                optimized_model_iter_fn = optimize_ctx
            else:
                if getattr(self, "hf_llm", False):
                    # If it's an llm, we want to optimize model.forward, and use
                    # the generate function
                    model = optimize_ctx(model)
                    optimized_model_iter_fn = self.model_iter_fn
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

            if experiment.func is coverage_experiment:
                ok, total = Stats.reset_counters()
                results = []
                # run with torch._dynamo few times to populate the cache
                for _ in range(3):
                    optimized_model_iter_fn(model, example_inputs)
                _, frames_second_pass = Stats.reset_counters()  # should be 0
                if frames_second_pass > 0:
                    optimized_model_iter_fn(model, example_inputs)
                    _, frames_third_pass = Stats.reset_counters()  # should be 0
                else:
                    frames_third_pass = 0

                results.append(
                    f"{ok:3}/{total:3} +{frames_third_pass} frames {compilation_time:3.0f}s"
                )

            experiment_kwargs["hf_llm"] = getattr(self, "hf_llm", False)

            results.append(
                experiment(
                    self.model_iter_fn, model, example_inputs, **experiment_kwargs
                )
            )
            return " ".join(map(str, results))