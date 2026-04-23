def __init__(
        self,
        model_args: "ModelArguments",
        data_args: "DataArguments",
        finetuning_args: "FinetuningArguments",
        generating_args: "GeneratingArguments",
    ) -> None:
        self.name = EngineName.SGLANG
        self.model_args = model_args
        config = load_config(model_args)  # may download model from ms hub
        if getattr(config, "quantization_config", None):  # gptq models should use float16
            quantization_config: dict[str, Any] = getattr(config, "quantization_config", None)
            quant_method = quantization_config.get("quant_method", "")
            if quant_method == QuantizationMethod.GPTQ and model_args.infer_dtype == "auto":
                model_args.infer_dtype = "float16"

        self.can_generate = finetuning_args.stage == "sft"
        tokenizer_module = load_tokenizer(model_args)
        self.tokenizer = tokenizer_module["tokenizer"]
        self.processor = tokenizer_module["processor"]
        self.tokenizer.padding_side = "left"
        self.template = get_template_and_fix_tokenizer(self.tokenizer, data_args)
        self.template.mm_plugin.expand_mm_tokens = False  # for sglang generate
        self.generating_args = generating_args.to_dict()
        if model_args.adapter_name_or_path is not None:
            self.lora_request = True
        else:
            self.lora_request = False

        launch_cmd = [
            "python3 -m sglang.launch_server",
            f"--model-path {model_args.model_name_or_path}",
            f"--dtype {model_args.infer_dtype}",
            f"--context-length {model_args.sglang_maxlen}",
            f"--mem-fraction-static {model_args.sglang_mem_fraction}",
            f"--tp-size {model_args.sglang_tp_size if model_args.sglang_tp_size != -1 else get_device_count() or 1}",
            f"--download-dir {model_args.cache_dir}",
            "--log-level error",
        ]
        if self.lora_request:
            launch_cmd.extend(
                [
                    "--max-loras-per-batch 1",
                    f"--lora-backend {model_args.sglang_lora_backend}",
                    f"--lora-paths lora0={model_args.adapter_name_or_path[0]}",
                    "--disable-radix-cache",
                ]
            )
        launch_cmd = " ".join(launch_cmd)
        logger.info_rank0(f"Starting SGLang server with command: {launch_cmd}")
        try:
            torch_gc()
            self.server_process, port = launch_server_cmd(launch_cmd)
            self.base_url = f"http://localhost:{port}"
            atexit.register(self._cleanup_server)

            logger.info_rank0(f"Waiting for SGLang server to be ready at {self.base_url}")
            wait_for_server(self.base_url, timeout=300)
            logger.info_rank0(f"SGLang server initialized successfully at {self.base_url}")
            try:
                response = requests.get(f"{self.base_url}/get_model_info", timeout=5)
                if response.status_code == 200:
                    model_info = response.json()
                    logger.info(f"SGLang server model info: {model_info}")
            except Exception as e:
                logger.debug(f"Note: could not get model info: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to start SGLang server: {str(e)}")
            self._cleanup_server()  # make sure to clean up any started process
            raise RuntimeError(f"SGLang server initialization failed: {str(e)}.")