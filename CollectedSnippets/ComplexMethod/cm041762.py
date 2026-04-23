def __init__(
        self,
        model_args: "ModelArguments",
        data_args: "DataArguments",
        finetuning_args: "FinetuningArguments",
        generating_args: "GeneratingArguments",
    ) -> None:
        self.name = EngineName.VLLM
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
        self.template.mm_plugin.expand_mm_tokens = False  # for vllm generate
        self.generating_args = generating_args.to_dict()

        engine_args = {
            "model": model_args.model_name_or_path,
            "trust_remote_code": model_args.trust_remote_code,
            "download_dir": model_args.cache_dir,
            "dtype": model_args.infer_dtype,
            "max_model_len": model_args.vllm_maxlen,
            "tensor_parallel_size": get_device_count() or 1,
            "gpu_memory_utilization": model_args.vllm_gpu_util,
            "disable_log_stats": True,
            "enforce_eager": model_args.vllm_enforce_eager,
            "enable_lora": model_args.adapter_name_or_path is not None,
            "max_lora_rank": model_args.vllm_max_lora_rank,
        }

        import vllm

        if version.parse(vllm.__version__) <= version.parse("0.10.0"):
            engine_args["disable_log_requests"] = True
        else:
            engine_args["enable_log_requests"] = False

        if self.template.mm_plugin.__class__.__name__ != "BasePlugin":
            engine_args["limit_mm_per_prompt"] = {"image": 4, "video": 2, "audio": 2}

        if isinstance(model_args.vllm_config, dict):
            engine_args.update(model_args.vllm_config)

        if getattr(config, "is_yi_vl_derived_model", None):
            import vllm.model_executor.models.llava

            logger.info_rank0("Detected Yi-VL model, applying projector patch.")
            vllm.model_executor.models.llava.LlavaMultiModalProjector = LlavaMultiModalProjectorForYiVLForVLLM

        self.model = AsyncLLMEngine.from_engine_args(AsyncEngineArgs(**engine_args))
        if model_args.adapter_name_or_path is not None:
            self.lora_request = LoRARequest("default", 1, model_args.adapter_name_or_path[0])
        else:
            self.lora_request = None