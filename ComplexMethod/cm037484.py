def check_and_update_config(cls, vllm_config: VllmConfig) -> None:
        model_config = vllm_config.model_config

        if model_config is not None:
            model_config.disable_cascade_attn = True

        cache_config = vllm_config.cache_config

        if not cache_config.user_specified_block_size:
            cache_config.block_size = 128

        if cache_config.block_size % 32 != 0:
            logger.warning(
                "CPU backend prefers block_size is multiples of 32, "
                "otherwise the performance is not optimized."
            )

        # Lagecy setting
        env_key = "VLLM_CPU_KVCACHE_SPACE"
        if env_key in os.environ and os.environ[env_key] != "":
            kv_cache_space = int(os.environ[env_key])
            cache_config.kv_cache_memory_bytes = kv_cache_space * GiB_bytes

        scheduler_config = vllm_config.scheduler_config
        # async scheduling is not required on CPU
        scheduler_config.async_scheduling = False
        if (
            scheduler_config.enable_chunked_prefill
            or cache_config.enable_prefix_caching
        ) and is_quantized_kv_cache(cache_config.cache_dtype):
            raise RuntimeError(
                "Chunked-prefill and prefix-cache on the CPU "
                "backend is not compatible with FP8 KV cache."
            )

        if is_quantized_kv_cache(cache_config.cache_dtype):
            logger.warning(
                "CPU backend doesn't support KV cache quantization fallback to auto."
            )
            cache_config.cache_dtype = "auto"

        parallel_config = vllm_config.parallel_config
        # OMP requires the MP executor to function correctly, UniProc is not
        # supported as it is not possible to set the OMP environment correctly
        if parallel_config.distributed_executor_backend == "uni":
            parallel_config.distributed_executor_backend = "mp"
        if parallel_config.worker_cls == "auto":
            parallel_config.worker_cls = "vllm.v1.worker.cpu_worker.CPUWorker"
        # Disable DBO
        if parallel_config.enable_dbo:
            logger.warning("Dual-Batch Overlap is not supported on CPU, disabled.")
            parallel_config.enable_dbo = False

        # Note: workaround for v1 gpu_model_runner
        from vllm.config import CompilationMode

        vllm_config.compilation_config.cudagraph_capture_sizes = []

        compilation_config = vllm_config.compilation_config
        if vllm_config.compilation_config.mode == CompilationMode.VLLM_COMPILE:
            # Note: vLLM V1 is using PIECEWISE level compilation, which will
            # take time to compile kernels just-in-time with the inductor
            # backend. For CPU CI tests, most of them are executed fast and
            # compilations consume too much time, even with torch compile
            # cache. So use VLLM_CPU_CI_ENV to indicate the CI environment,
            # and just execute model with dynamo + eager mode to save time.
            # VLLM_CPU_CI_ENV is only used as an internal variable.
            if os.environ.get("VLLM_CPU_CI_ENV", "0") != "0":
                backend = "eager"
            else:
                backend = "inductor"

            compilation_config.mode = CompilationMode.DYNAMO_TRACE_ONCE
            compilation_config.backend = backend
            compilation_config.inductor_compile_config.update(
                {
                    "dce": True,
                    "size_asserts": False,
                    "nan_asserts": False,
                    "epilogue_fusion": True,
                    "cpp.dynamic_threads": True,
                }
            )
            compilation_config.ir_enable_torch_wrap = False

        if vllm_config.lora_config is not None:
            compilation_config.mode = CompilationMode.NONE

        if (
            cls.get_cpu_architecture() == CpuArchEnum.ARM
            and "+gelu" not in compilation_config.custom_ops
            and "-gelu" not in compilation_config.custom_ops
        ):
            compilation_config.custom_ops.append("+gelu")

        vllm_config.profiler_config.torch_profiler_dump_cuda_time_total = False

        assert vllm_config.device_config.device_type == "cpu"

        #
        # Environment variables for CPU executor
        #

        os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

        # Note: to avoid the error 'nthreads cannot be larger than environment
        # variable "NUMEXPR_MAX_THREADS" (64)'.
        os.environ["NUMEXPR_MAX_THREADS"] = str(get_max_threads())

        # Disable torch async compiling which won't work with daemonic processes
        os.environ["TORCHINDUCTOR_COMPILE_THREADS"] = "1"

        # Disable multi-stream for shared experts as no Stream on CPU
        os.environ["VLLM_DISABLE_SHARED_EXPERTS_STREAM"] = "1"

        # Avoid inductor generates num_thread() and breaks the thread binding
        os.environ["TORCHINDUCTOR_CPP_DYNAMIC_THREADS"] = "1"

        ld_preload_str = os.getenv("LD_PRELOAD", "")
        cpu_architecture = Platform.get_cpu_architecture()

        if (
            platform.system() == "Linux"
            and cpu_architecture
            in (CpuArchEnum.ARM, CpuArchEnum.POWERPC, CpuArchEnum.X86)
            and not (
                "libomp" in ld_preload_str
                or "libgomp" in ld_preload_str
                or "libiomp" in ld_preload_str
            )
        ):
            # We need to LD_PRELOAD PyTorch's libgomp, otherwise only
            # one core will be properly utilized when we thread-bind
            # See: https://github.com/vllm-project/vllm/issues/27369
            # TODO: Remove once:
            # https://github.com/pytorch/pytorch/issues/166087 is fixed

            # We need to find the location of PyTorch's libgomp
            torch_pkg = os.path.dirname(torch.__file__)
            site_root = os.path.dirname(torch_pkg)
            # Search both torch.libs and torch/lib - See:
            # https://github.com/vllm-project/vllm/issues/30470
            torch_libs_paths = [
                os.path.join(site_root, "torch.libs"),
                os.path.join(torch_pkg, "lib"),
            ]
            pytorch_libgomp_so_candidates = []
            for torch_libs in torch_libs_paths:
                pytorch_libgomp_so_candidates.extend(
                    glob.glob(os.path.join(torch_libs, "libgomp*.so*"))
                )
            if pytorch_libgomp_so_candidates:
                pytorch_libgomp_so = pytorch_libgomp_so_candidates[0]
                if ld_preload_str:
                    ld_preload_str += ":"
                ld_preload_str += pytorch_libgomp_so
                os.environ["LD_PRELOAD"] = ld_preload_str

        # LD_PRELOAD libtcmalloc, bundled under vllm/libs to reduce
        # memory allocation overhead
        if (
            platform.system() == "Linux"
            and cpu_architecture in (CpuArchEnum.ARM, CpuArchEnum.X86)
            and "libtcmalloc" not in ld_preload_str
        ):
            vllm_pkg = os.path.dirname(os.path.dirname(__file__))
            tcmalloc_so = None
            for pattern in ("libtcmalloc_minimal*.so*", "libtcmalloc.so*"):
                tcmalloc_so_candidates = glob.glob(
                    os.path.join(vllm_pkg, "libs", pattern)
                )
                if tcmalloc_so_candidates:
                    tcmalloc_so = tcmalloc_so_candidates[0]
                    break

            if tcmalloc_so is not None:
                if ld_preload_str:
                    ld_preload_str = f"{tcmalloc_so}:{ld_preload_str}"
                else:
                    ld_preload_str = tcmalloc_so
                os.environ["LD_PRELOAD"] = ld_preload_str

        os.environ["LOCAL_WORLD_SIZE"] = str(
            vllm_config.parallel_config.tensor_parallel_size
        )

        if model_config is not None and model_config.use_mla:
            logger.info(
                "MLA is enabled on a non-GPU platform; forcing chunked "
                "prefill and prefix caching to be disabled."
            )
            vllm_config.scheduler_config.enable_chunked_prefill = False
            vllm_config.scheduler_config.max_num_batched_tokens = max(
                vllm_config.model_config.max_model_len,
                vllm_config.scheduler_config.DEFAULT_MAX_NUM_BATCHED_TOKENS,
            )