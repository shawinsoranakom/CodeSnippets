def get_model(
        self,
        backend: str,
        model_path: str | None,
        server_url: str | None,
        **kwargs,
    ) -> MinerUClient:
        key = (backend, model_path, server_url)
        with self._lock:
            if key not in self._models:
                start_time = time.time()
                model = None
                processor = None
                vllm_llm = None
                lmdeploy_engine = None
                vllm_async_llm = None
                batch_size = kwargs.get("batch_size", 0)  # for transformers backend only
                max_concurrency = kwargs.get("max_concurrency", 100)  # for http-client backend only
                http_timeout = kwargs.get("http_timeout", 600)  # for http-client backend only
                server_headers = kwargs.get("server_headers", None)  # for http-client backend only
                max_retries = kwargs.get("max_retries", 3)  # for http-client backend only
                retry_backoff_factor = kwargs.get("retry_backoff_factor", 0.5)  # for http-client backend only
                # 从kwargs中移除这些参数，避免传递给不相关的初始化函数
                for param in ["batch_size", "max_concurrency", "http_timeout", "server_headers", "max_retries", "retry_backoff_factor"]:
                    if param in kwargs:
                        del kwargs[param]
                if backend not in ["http-client"] and not model_path:
                    model_path = auto_download_and_get_model_root_path("/","vlm")
                if backend == "transformers":
                    try:
                        from transformers import (
                            AutoProcessor,
                            Qwen2VLForConditionalGeneration,
                        )
                        from transformers import __version__ as transformers_version
                    except ImportError:
                        raise ImportError("Please install transformers to use the transformers backend.")

                    if version.parse(transformers_version) >= version.parse("4.56.0"):
                        dtype_key = "dtype"
                    else:
                        dtype_key = "torch_dtype"
                    device = get_device()
                    model = Qwen2VLForConditionalGeneration.from_pretrained(
                        model_path,
                        device_map={"": device},
                        **{dtype_key: "auto"},  # type: ignore
                    )
                    processor = AutoProcessor.from_pretrained(
                        model_path,
                        use_fast=True,
                    )
                    if batch_size == 0:
                        batch_size = set_default_batch_size()
                elif backend == "mlx-engine":
                    mlx_supported = is_mac_os_version_supported()
                    if not mlx_supported:
                        raise EnvironmentError("mlx-engine backend is only supported on macOS 13.5+ with Apple Silicon.")
                    from mineru_vl_utils.mlx_compat import load_mlx_model
                    model, processor = load_mlx_model(model_path)
                else:
                    if os.getenv('OMP_NUM_THREADS') is None:
                        os.environ["OMP_NUM_THREADS"] = "1"

                    if backend == "vllm-engine":
                        try:
                            import vllm
                        except ImportError:
                            raise ImportError("Please install vllm to use the vllm-engine backend.")

                        kwargs = mod_kwargs_by_device_type(kwargs, vllm_mode="sync_engine")

                        if "compilation_config" in kwargs:
                            if isinstance(kwargs["compilation_config"], str):
                                try:
                                    kwargs["compilation_config"] = json.loads(kwargs["compilation_config"])
                                except json.JSONDecodeError:
                                    logger.warning(
                                        f"Failed to parse compilation_config as JSON: {kwargs['compilation_config']}")
                                    del kwargs["compilation_config"]
                        if "gpu_memory_utilization" not in kwargs:
                            kwargs["gpu_memory_utilization"] = set_default_gpu_memory_utilization()
                        if "model" not in kwargs:
                            kwargs["model"] = model_path
                        if enable_custom_logits_processors() and ("logits_processors" not in kwargs):
                            from mineru_vl_utils import MinerULogitsProcessor
                            kwargs["logits_processors"] = [MinerULogitsProcessor]
                        # 使用kwargs为 vllm初始化参数
                        vllm_llm = vllm.LLM(**kwargs)
                    elif backend == "vllm-async-engine":
                        try:
                            from vllm.engine.arg_utils import AsyncEngineArgs
                            from vllm.v1.engine.async_llm import AsyncLLM
                            from vllm.config import CompilationConfig
                        except ImportError:
                            raise ImportError("Please install vllm to use the vllm-async-engine backend.")

                        kwargs = mod_kwargs_by_device_type(kwargs, vllm_mode="async_engine")

                        if "compilation_config" in kwargs:
                            if isinstance(kwargs["compilation_config"], dict):
                                # 如果是字典，转换为 CompilationConfig 对象
                                kwargs["compilation_config"] = CompilationConfig(**kwargs["compilation_config"])
                            elif isinstance(kwargs["compilation_config"], str):
                                # 如果是 JSON 字符串，先解析再转换
                                try:
                                    config_dict = json.loads(kwargs["compilation_config"])
                                    kwargs["compilation_config"] = CompilationConfig(**config_dict)
                                except (json.JSONDecodeError, TypeError) as e:
                                    logger.warning(
                                        f"Failed to parse compilation_config: {kwargs['compilation_config']}, error: {e}")
                                    del kwargs["compilation_config"]
                        if "gpu_memory_utilization" not in kwargs:
                            kwargs["gpu_memory_utilization"] = set_default_gpu_memory_utilization()
                        if "model" not in kwargs:
                            kwargs["model"] = model_path
                        if enable_custom_logits_processors() and ("logits_processors" not in kwargs):
                            from mineru_vl_utils import MinerULogitsProcessor
                            kwargs["logits_processors"] = [MinerULogitsProcessor]
                        # 使用kwargs为 vllm初始化参数
                        vllm_async_llm = AsyncLLM.from_engine_args(AsyncEngineArgs(**kwargs))
                    elif backend == "lmdeploy-engine":
                        try:
                            from lmdeploy import PytorchEngineConfig, TurbomindEngineConfig
                            from lmdeploy.serve.vl_async_engine import VLAsyncEngine
                        except ImportError:
                            raise ImportError("Please install lmdeploy to use the lmdeploy-engine backend.")
                        if "cache_max_entry_count" not in kwargs:
                            kwargs["cache_max_entry_count"] = 0.5

                        device_type = os.getenv("MINERU_LMDEPLOY_DEVICE", "")
                        if device_type == "":
                            if "lmdeploy_device" in kwargs:
                                device_type = kwargs.pop("lmdeploy_device")
                                if device_type not in ["cuda", "ascend", "maca", "camb"]:
                                    raise ValueError(f"Unsupported lmdeploy device type: {device_type}")
                            else:
                                device_type = "cuda"
                        lm_backend = os.getenv("MINERU_LMDEPLOY_BACKEND", "")
                        if lm_backend == "":
                            if "lmdeploy_backend" in kwargs:
                                lm_backend = kwargs.pop("lmdeploy_backend")
                                if lm_backend not in ["pytorch", "turbomind"]:
                                    raise ValueError(f"Unsupported lmdeploy backend: {lm_backend}")
                            else:
                                lm_backend = set_lmdeploy_backend(device_type)
                        logger.info(f"lmdeploy device is: {device_type}, lmdeploy backend is: {lm_backend}")

                        if lm_backend == "pytorch":
                            kwargs["device_type"] = device_type
                            backend_config = PytorchEngineConfig(**kwargs)
                        elif lm_backend == "turbomind":
                            backend_config = TurbomindEngineConfig(**kwargs)
                        else:
                            raise ValueError(f"Unsupported lmdeploy backend: {lm_backend}")

                        log_level = 'ERROR'
                        from lmdeploy.utils import get_logger
                        lm_logger = get_logger('lmdeploy')
                        lm_logger.setLevel(log_level)
                        if os.getenv('TM_LOG_LEVEL') is None:
                            os.environ['TM_LOG_LEVEL'] = log_level

                        lmdeploy_engine = VLAsyncEngine(
                            model_path,
                            backend=lm_backend,
                            backend_config=backend_config,
                        )
                predictor = MinerUClient(
                    backend=backend,
                    model=model,
                    processor=processor,
                    lmdeploy_engine=lmdeploy_engine,
                    vllm_llm=vllm_llm,
                    vllm_async_llm=vllm_async_llm,
                    server_url=server_url,
                    batch_size=batch_size,
                    max_concurrency=max_concurrency,
                    http_timeout=http_timeout,
                    server_headers=server_headers,
                    max_retries=max_retries,
                    retry_backoff_factor=retry_backoff_factor,
                    enable_table_formula_eq_wrap=True,
                    image_analysis=True,
                    enable_cross_page_table_merge=True,
                )
                predictor._mineru_runtime_handles = {
                    "backend": backend,
                    "model": model,
                    "processor": processor,
                    "vllm_llm": vllm_llm,
                    "vllm_async_llm": vllm_async_llm,
                    "lmdeploy_engine": lmdeploy_engine,
                }
                _maybe_enable_serial_execution(predictor, backend)
                self._models[key] = predictor
                elapsed = round(time.time() - start_time, 2)
                logger.info(f"get {backend} predictor cost: {elapsed}s")
        return self._models[key]