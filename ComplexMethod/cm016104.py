def run(runner, args, original_dir=None):
    # Pass the parsed args object to benchmark runner object
    torch._dynamo.reset()
    runner.args = args

    args.filter = args.filter or [r"."]
    args.exclude = args.exclude or [r"^$"]
    args.exclude_exact = args.exclude_exact or []

    if args.inductor:
        if args.backend is not None:
            raise AssertionError(f"--inductor conflicts with --backend={args.backend}")
        args.backend = "inductor"
    if args.optimus:
        if args.backend is not None:
            raise AssertionError(f"--optimus conflicts with --backend={args.backend}")
        args.backend = "optimus"
    if args.quantization:
        if args.backend is not None:
            raise AssertionError(
                f"--quantization conflicts with --backend={args.backend}"
            )
        args.backend = "torchao"
    if args.dynamic_batch_only:
        args.dynamic_shapes = True
        torch._dynamo.config.assume_static_by_default = True
    if args.unbacked_batch_only:
        args.dynamic_shapes = True
        torch._dynamo.config.assume_static_by_default = True
    if args.dynamic_shapes:
        if not args.dynamic_batch_only and not args.unbacked_batch_only:
            torch._dynamo.config.assume_static_by_default = False
    if args.compiled_autograd:
        torch._dynamo.config.compiled_autograd = True
    if args.propagate_real_tensors:
        # TODO: Separate flag for data dependent
        torch._dynamo.config.capture_scalar_outputs = True
        torch._dynamo.config.capture_dynamic_output_shape_ops = True
        torch._functorch.config.fake_tensor_propagate_real_tensors = True
    if args.specialize_int:
        torch._dynamo.config.specialize_int = True
    if args.ci:
        if args.accuracy:
            # Run fewer iterations when checking accuracy
            args.repeat = min(args.repeat, 2)

            # Set translation validation on by default on CI accuracy runs.
            torch.fx.experimental._config.translation_validation = True

    if args.ddp:
        if not args.training:
            raise AssertionError("DDP benchmark requires --training mode")
        torch._dynamo.config.optimize_ddp = args.optimize_ddp_mode
        if args.only == "dlrm":
            log.error(
                "DLRM+DDP is unsupported as it requires sharding the embedding layer separately from DDP"
            )
            return sys.exit(-1)
    if args.deterministic and not args.accuracy:
        setup_determinism(args)

    if args.accuracy:
        # Use small batch size. We use >1 batch size to ensure we test
        # batch_norm type of operators that work on batch dims.
        # TODO - Go through the failures for batch size = 2
        if args.batch_size is None:
            if args.batch_invariant:
                if runner.suite_name == "huggingface":
                    args.batch_size = 8
                elif runner.suite_name == "torchbench":
                    args.batch_size = 8
                else:
                    args.batch_size = 16
            elif runner.suite_name == "huggingface":
                args.batch_size = 1
            elif runner.suite_name == "torchbench":
                args.batch_size = 4
            else:
                # Larger batch size of TIMM models to have stable batch_norm
                if runner.suite_name != "timm_models":
                    raise AssertionError(
                        f"expected runner.suite_name to be 'timm_models', got {runner.suite_name}"
                    )
                args.batch_size = 8

        # Remove sources of randomness
        if runner.suite_name not in ("timm_models", "huggingface"):
            # TODO - Using train mode for timm_models and HF models. Move to train mode for Torchbench as well.
            args.use_eval_mode = True
        inductor_config.fallback_random = True

        setup_determinism(args)
        if args.batch_invariant:
            setup_batch_invariant(args)

        if args.only is not None and args.only in {
            "nvidia_deeprecommender",
        }:
            # These seem unhappy with numerics of larger cuBLASLt workspace
            torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
            torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False

        # Some models e.g. yolov3 assert batch size on n_gpus
        if "CUDA_VISIBLE_DEVICES" not in os.environ and not args.multiprocess:
            args.device_index = "0"

        # Stricter check to disable fallbacks
        args.suppress_errors = False

        if not args.disable_cudagraphs:
            runner.skip_models.update(
                {
                    # xfail: https://github.com/pytorch/pytorch/issues/145773
                    "llama",
                    "cm3leon_generate",
                    "modded_nanogpt",
                }
            )

    if args.device_index is not None:
        if args.multiprocess:
            print("Cannot specify both --device_index and --multiprocess")
            return sys.exit(-1)
        os.environ["CUDA_VISIBLE_DEVICES"] = args.device_index

    elif args.performance:
        # Ensure that we test on real scenarios
        args.use_eval_mode = False

    if args.partition_id > args.total_partitions or args.partition_id < 0:
        print("Invalid partition id")
        return sys.exit(-1)

    if not args.devices:
        if torch.cuda.is_available():
            args.devices = ["cuda"]
        else:
            log.warning("torch.cuda.is_available() == False, using CPU")
            args.devices = ["cpu"]

    if args.devices != ["cpu"] and (HAS_CUDA or HAS_XPU):
        global synchronize
        synchronize = torch.cuda.synchronize if HAS_CUDA else torch.xpu.synchronize

    if args.nnc:
        torch._C._jit_override_can_fuse_on_cpu(True)
        torch._C._jit_override_can_fuse_on_gpu(True)
        torch._C._jit_set_texpr_fuser_enabled(True)
        torch._C._jit_set_nvfuser_enabled(False)

    if args.threads:
        torch.set_num_threads(args.threads)

    if args.verbose:
        torch._logging.set_logs(dynamo=logging.DEBUG)

    if args.print_graph_breaks:
        torch._logging.set_logs(graph_breaks=True)

    if args.quiet:
        torch._logging.set_logs(dynamo=logging.ERROR)

    torch._dynamo.config.suppress_errors = args.suppress_errors

    if args.training:
        runner.model_iter_fn = runner.forward_and_backward_pass
        runner.skip_models.update(runner.skip_not_suitable_for_training_models)
    else:
        runner.model_iter_fn = runner.forward_pass

    if args.fast:
        runner.skip_models.update(runner.slow_models)

    if args.devices == ["cpu"]:
        arch = platform.machine()
        runner.skip_models.update(runner.skip_models_for_cpu)
        if arch == "aarch64":
            runner.skip_models.update(runner.skip_models_for_cpu_aarch64)
    elif args.devices == ["cuda"]:
        runner.skip_models.update(runner.skip_models_for_cuda)
    elif args.devices == ["xpu"]:
        runner.skip_models.update(runner.skip_models_for_xpu)

    if not args.multiprocess:
        runner.skip_models.update(runner.skip_multiprocess_models)

    if args.freezing:
        if args.devices == ["cpu"]:
            runner.skip_models.update(runner.skip_models_for_freezing_cpu)
        elif args.devices == ["cuda"]:
            runner.skip_models.update(runner.skip_models_for_freezing_cuda)

    if args.no_skip:
        runner.skip_models.clear()

    experiment = null_experiment
    global \
        current_name, \
        current_device, \
        current_batch_size, \
        current_backend, \
        current_mode, \
        current_dtype, \
        current_quantization, \
        current_settings, \
        output_filename, \
        disable_output, \
        optimize_ctx
    optimize_ctx = contextlib.nullcontext()

    if args.disable_output:
        disable_output = True

    if args.overhead:
        optimize_ctx = torch._dynamo.optimize(dummy_fx_compile, nopython=args.nopython)
        experiment = speedup_experiment
        output_filename = "overheads.csv"
    elif args.inductor:
        inductor_config.debug = args.verbose
        if args.threads:
            inductor_config.cpp.threads = args.threads

        optimize_ctx = functools.partial(
            torch.compile,
            backend="inductor",
            fullgraph=args.nopython,
            mode=args.inductor_compile_mode,
        )
        experiment = speedup_experiment
        output_filename = "inductor.csv"
    elif args.export:
        optimize_ctx = export
        experiment = speedup_experiment
        output_filename = "export.csv"
    elif args.aot_precompile:
        optimize_ctx = aot_precompile
        experiment = speedup_experiment
        output_filename = "aot_precompile.csv"
    elif args.export_nativert:
        optimize_ctx = export_nativert
        experiment = speedup_experiment
        output_filename = "export_nativert.csv"
    elif args.torchscript_jit_trace:
        optimize_ctx = torchscript_jit_trace
        experiment = speedup_experiment
        output_filename = "torchscript_jit_trace.csv"
    elif args.xla:
        (dev,) = args.devices
        os.environ["PJRT_DEVICE"] = {"cuda": "GPU", "cpu": "CPU"}[dev]
        torch._dynamo.mark_dynamic = MagicMock()
        experiment = xla
        output_filename = "xla.csv"
    elif args.speedup_dynamo_ts:
        optimize_ctx = torch._dynamo.optimize("ts", nopython=args.nopython)
        experiment = speedup_experiment
        output_filename = "speedup_dynamo_ts.csv"
    elif args.prims_nvfuser:
        optimize_ctx = torch._dynamo.optimize("prims_nvfuser", nopython=args.nopython)
        experiment = speedup_experiment
        backend_str = "prims_nvfuser"
        output_filename = f"accuracy_aot_{backend_str}.csv"
    elif args.print_fx:
        optimize_ctx = torch._dynamo.optimize(
            print_fx,
            nopython=args.nopython,
        )
    elif args.print_aten_ops:
        optimize_ctx = torch._dynamo.optimize(
            print_aten_ops,
            nopython=args.nopython,
        )
    elif args.nothing:
        optimize_ctx = nothing
        experiment = speedup_experiment
        output_filename = "nothing.csv"
    elif args.backend or args.export_aot_inductor:
        if args.export_aot_inductor:
            if args.training:
                raise AssertionError("AOTInductor only supports inference")
            optimize_ctx = functools.partial(
                export_aot_inductor, mode=args.inductor_compile_mode
            )

            # AOTInductor doesn't support control flow yet
            runner.skip_models.update(runner.skip_models_due_to_control_flow)
            runner.skip_models.update(runner.skip_models_due_to_export_not_supported)
        elif args.backend == "torchao":
            if "cuda" not in args.devices:
                raise AssertionError(
                    f"Quantization requires CUDA device, got devices={args.devices}"
                )
            if not args.bfloat16:
                raise AssertionError("Quantization requires dtype bfloat16")
            try:
                from torchao_backend import setup_baseline, torchao_optimize_ctx
            except ImportError:
                try:
                    from .torchao_backend import setup_baseline, torchao_optimize_ctx
                except ImportError:
                    from userbenchmark.dynamo.dynamobench.torchao_backend import (
                        setup_baseline,
                        torchao_optimize_ctx,
                    )

            setup_baseline()
            baseline_ctx = functools.partial(
                torch.compile,
                backend="inductor",
                fullgraph=args.nopython,
                mode=args.inductor_compile_mode,
            )
            model_iter_fn = baseline_ctx(runner.model_iter_fn)

            # needed to avoid CUDAGraph fast-path warning / inconsistent timing when prior
            # outputs still require backward (see torch._inductor.cudagraph_trees)
            def model_iter_fn_and_mark_step(*args, **kwargs):
                torch.compiler.cudagraph_mark_step_begin()
                model_iter_fn(*args, **kwargs)

            runner.model_iter_fn = model_iter_fn_and_mark_step
            optimize_ctx = torchao_optimize_ctx(args.quantization)
        elif args.backend == "optimus":
            from .optimus import get_baseline_ctx, get_optimus_optimize_ctx

            baseline_ctx = get_baseline_ctx(
                nopython=args.nopython, inductor_compile_mode=args.inductor_compile_mode
            )
            runner.model_iter_fn = baseline_ctx(runner.model_iter_fn)
            optimize_ctx = get_optimus_optimize_ctx(
                args.optimus, args.nopython, args.inductor_compile_mode
            )
        else:
            optimize_ctx = torch._dynamo.optimize(args.backend, nopython=args.nopython)
        experiment = (
            speedup_experiment
            if args.backend not in ["torchao", "optimus"]
            else latency_experiment
        )
        if args.accuracy:
            output_filename = f"accuracy_{args.backend}.csv"
        elif args.tolerance:
            output_filename = f"tolerance_{args.backend}.csv"
        else:
            output_filename = f"speedup_{args.backend}.csv"
    elif args.recompile_profiler:
        output_filename = "recompile_profiler_log.csv"
        experiment = recompile_profiler_experiment
    else:
        optimize_ctx = torch._dynamo.optimize(
            fx_insert_profiling, nopython=args.nopython
        )
        experiment = coverage_experiment
        output_filename = "coverage.csv"

    if args.only in runner.disable_cudagraph_models:
        args.disable_cudagraphs = True

    if (
        args.inductor
        or args.backend == "inductor"
        or args.export_aot_inductor
        or args.backend == "optimus"
    ):
        inductor_config.triton.cudagraphs = not args.disable_cudagraphs
        inductor_config.triton.persistent_reductions = (
            not args.disable_persistent_reductions
        )
        inductor_config.split_reductions = not args.disable_split_reductions
        inductor_config.triton.divisible_by_16 = not args.disable_divisible_by_16
        if args.inference:
            inductor_config.freezing = args.freezing
        if args.inductor_config:
            for config in args.inductor_config:
                key, value = config.split("=")
                typ = type(inductor_config.__getattr__(key))
                if issubclass(typ, bool):
                    if value not in ("0", "1", "True", "False"):
                        raise AssertionError(
                            f"expected bool value for {key}, got {value}"
                        )
                    value = value in ("1", "True")
                elif issubclass(typ, (str, int, float)):
                    value = typ(value)
                else:
                    raise NotImplementedError(typ)
                inductor_config.__setattr__(key, value)

    runner.setup_amp()

    if args.output:
        output_filename = args.output

    if output_filename:
        if args.output_directory:
            output_filename = os.path.join(args.output_directory, output_filename)
        else:
            output_filename = os.path.join(
                torch._dynamo.config.base_dir, output_filename
            )

    if args.find_batch_sizes and args.only:
        for device in args.devices:
            batch_size = runner.batch_size_finder(device, args.only)
            print(args.only, batch_size)
            write_outputs(output_filename, [], [args.only, batch_size])
        return

    should_profile_details = args.profile_details
    args.profile_details = {}
    if args.export_profiler_trace:
        if should_profile_details:
            args.profile_details = {
                "record_shapes": True,
                "profile_memory": True,
                "with_stack": True,
                "with_modules": True,
                "activities": [
                    torch.profiler.ProfilerActivity.CPU,
                    torch.profiler.ProfilerActivity.CUDA,
                ],
            }

        if args.profiler_trace_name is None:
            if args.backend:
                args.profiler_trace_name = args.backend
            elif args.inductor:
                args.profiler_trace_name = "inductor"
            else:
                args.profiler_trace_name = "profile"
        else:
            args.profiler_trace_name = args.profiler_trace_name

    if args.no_translation_validation:
        # Overwrite 'translation_validation' config, if specified.
        torch.fx.experimental._config.translation_validation = False

    experiment = functools.partial(experiment, args)

    if args.only and should_diff_branch(args):
        import git

        repo = git.Repo()
        main_branch = repo.active_branch.name
        try:
            # Adding diff-branch again to the args will override previous value
            call_args = (
                [sys.executable] + sys.argv + [f"--diff-branch={diff_branch_default}"]
            )
            # Run for main branch
            subprocess.check_call(call_args + [f"--tag={main_branch}"])
            # Run for comparison branch
            repo.git.checkout(args.diff_branch)
            subprocess.check_call(call_args + [f"--tag={args.diff_branch}"])
        finally:
            # Go back to main branch
            repo.git.checkout(main_branch)
    elif args.only:
        model_name = args.only
        for device in args.devices:
            batch_size = args.batch_size
            if args.batch_size_file:
                batch_size = read_batch_size_from_file(
                    args, args.batch_size_file, model_name
                )
            if model_specified_by_path(args.only):
                model, example_inputs = load_model_from_path(args.only)
                name = model.__class__.__name__
                model = model.to(device=device)
                example_inputs = tree_map_only(
                    torch.Tensor, lambda x: x.to(device=device), example_inputs
                )
            else:
                name = model_name
                try:
                    with tqdm(desc="loading model"):
                        extra_args = []
                        if hasattr(args, "rank") and hasattr(args, "world_size"):
                            extra_args += [
                                "--rank",
                                str(args.rank),
                                "--world_size",
                                str(args.world_size),
                            ]

                        if args.part:
                            (
                                device,
                                name,
                                model,
                                example_inputs,
                                batch_size,
                            ) = runner.load_model(
                                device,
                                model_name,
                                batch_size=batch_size,
                                part=args.part,
                                extra_args=extra_args,
                            )
                        else:
                            if args.fsdp:
                                # Always load model on cpu for fsdp
                                # When initializing FSDP, we will use the cuda device if args.cuda is set
                                (
                                    _,
                                    name,
                                    model,
                                    example_inputs,
                                    batch_size,
                                ) = runner.load_model(
                                    "cpu",
                                    model_name,
                                    batch_size=batch_size,
                                    extra_args=extra_args,
                                )
                            else:
                                (
                                    device,
                                    name,
                                    model,
                                    example_inputs,
                                    batch_size,
                                ) = runner.load_model(
                                    device,
                                    model_name,
                                    batch_size=batch_size,
                                    extra_args=extra_args,
                                )
                except Exception as e:
                    import traceback

                    mode = "train" if args.training else "eval"
                    print(f"{device:4} {mode:5} {name:34} ")
                    print(traceback.format_exc())
                    status = (
                        "model_fail_to_load"
                        if isinstance(e, NotImplementedError)
                        else "eager_fail_to_run"
                    )
                    write_csv_when_exception(args, name, status, device)
                    # NB: current_name/current_device not set, so pass
                    # explicitly
                    output_signpost(
                        {"name": name, "dev": device},
                        args,
                        runner.suite_name,
                        error=status,
                    )
                    continue  # bad benchmark implementation

            if args.trace_on_xla:
                xla_dev = xm.xla_device()
                model = model.to(device=xla_dev)
                example_inputs = tree_map_only(
                    torch.Tensor, lambda x: x.to(device=xla_dev), example_inputs
                )

            current_name = name
            current_device = device
            current_batch_size = batch_size
            current_backend = args.backend
            current_mode = (
                "training" if args.training else "inference" if args.inference else ""
            )
            if args.float16:
                current_dtype = "float16"
            elif args.bfloat16:
                current_dtype = "bfloat16"
            elif args.float32:
                current_dtype = "float32"
            elif args.amp:
                current_dtype = "amp"
            else:
                current_dtype = ""
            current_quantization = args.quantization
            # Keep the remaining of the settings
            current_settings = vars(args)
            set_model_name(name)

            # Look for stuff that looks like batch size, and mark it dynamic.
            # Better integration would integrate directly with benchmark suite
            # but cannot conveniently do this
            # NB: This must be done late enough so that we don't do more
            # conversions on the inputs
            # NB: Assumes only the first batch-y like dimension is the batch
            marked = False

            def detect_and_mark_batch(t, use_unbacked=False):
                nonlocal marked
                for i, s in enumerate(t.size()):
                    if s == batch_size:
                        if use_unbacked:
                            # Use duck_shape_id="batch" so all batch dimensions
                            # share the same unbacked symbol
                            torch._dynamo.decorators.mark_unbacked(
                                t, i, shape_id="batch", hint_override=batch_size, min=1
                            )
                        else:
                            torch._dynamo.maybe_mark_dynamic(t, i)
                        marked = True
                        break

            if (
                (args.dynamic_batch_only or args.unbacked_batch_only)
                and batch_size > 1
                and model_name not in CI_SKIP_DYNAMIC_BATCH_ONLY
            ):
                mark_fn = functools.partial(
                    detect_and_mark_batch, use_unbacked=args.unbacked_batch_only
                )
                tree_map_only(torch.Tensor, mark_fn, example_inputs)
                if not marked:
                    raise AssertionError(
                        f"nothing in example_inputs had a dim with {batch_size}"
                    )

            if args.log_operator_inputs:
                log_operator_inputs(
                    model, example_inputs, runner.model_iter_fn, name, args
                )
                continue

            if args.per_process_memory_fraction != 1:
                torch.cuda.set_per_process_memory_fraction(
                    args.per_process_memory_fraction
                )
            if model_name in DO_NOT_CAST_INPUTS:
                model, _ = runner.cast_based_on_args(model, example_inputs)

            else:
                model, example_inputs = runner.cast_based_on_args(model, example_inputs)
            runner.setup_amp(current_device)
            guard_ctx = contextlib.nullcontext()
            if name in runner.guard_on_nn_module_models:
                guard_ctx = torch._dynamo.config.patch(guard_nn_modules=True)

            with guard_ctx:
                runner.run_one_model(
                    name,
                    model,
                    example_inputs,
                    optimize_ctx,
                    experiment,
                    explain=args.explain,
                    tag=args.tag,
                    batch_size=batch_size if args.dynamic_batch_only else None,
                )
        if args.generate_aot_autograd_stats:
            stats_file = output_filename.split(".csv")[0] + "_stats.csv"
            write_outputs(
                stats_file,
                ("dev", "name", "batch_size", "total_aot_graphs", "ok_aot_graphs"),
                [
                    current_device,
                    current_name,
                    current_batch_size,
                    *Stats.aot_summary(),
                ],
            )
    else:
        metrics.purge_old_log_files()
        if (
            output_filename
            and os.path.exists(output_filename)
            and not args.retain_output
        ):
            os.unlink(output_filename)
        if original_dir:
            os.chdir(original_dir)
        model_names = list(runner.iter_model_names(args))
        nmodels = len(model_names)
        for i, name in enumerate(model_names):
            current_name = name
            if args.progress:
                print(f"Running model {i + 1}/{nmodels}", flush=True)

            try:
                timeout = args.timeout
                if should_diff_branch(args):
                    timeout *= 2
                env = os.environ.copy()
                if args.ci and name in CI_PRESERVE_COMPILE_DEBUG:
                    env["TORCH_COMPILE_DEBUG"] = "1"
                subprocess.check_call(
                    [sys.executable] + sys.argv + [f"--only={name}"],
                    timeout=timeout,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                write_csv_when_exception(args, name, "timeout")
                # NB: device is potentially multiple here, though we should
                # try our best to report in anyway TODO
                output_signpost(
                    {"name": name}, args, runner.suite_name, error="timeout"
                )
            except subprocess.CalledProcessError as e:
                print("Run failed with return code: ", e.returncode, file=sys.stderr)
                print("Output: ", e.output, file=sys.stderr)
                print("Error: ", e.stderr, file=sys.stderr)
        print_summary(output_filename, print_dataframe=args.print_dataframe_summary)