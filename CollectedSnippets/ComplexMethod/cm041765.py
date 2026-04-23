def __init__(self, args: Optional[dict[str, Any]] = None) -> None:
        model_args, data_args, finetuning_args, generating_args = get_infer_args(args)

        if model_args.infer_backend == EngineName.HF:
            from .hf_engine import HuggingfaceEngine

            self.engine: BaseEngine = HuggingfaceEngine(model_args, data_args, finetuning_args, generating_args)
        elif model_args.infer_backend == EngineName.VLLM:
            try:
                from .vllm_engine import VllmEngine

                self.engine: BaseEngine = VllmEngine(model_args, data_args, finetuning_args, generating_args)
            except ImportError as e:
                raise ImportError(
                    "vLLM not install, you may need to run `pip install vllm`\n"
                    "or try to use HuggingFace backend: --infer_backend huggingface"
                ) from e
        elif model_args.infer_backend == EngineName.SGLANG:
            try:
                from .sglang_engine import SGLangEngine

                self.engine: BaseEngine = SGLangEngine(model_args, data_args, finetuning_args, generating_args)
            except ImportError as e:
                raise ImportError(
                    "SGLang not install, you may need to run `pip install sglang[all]`\n"
                    "or try to use HuggingFace backend: --infer_backend huggingface"
                ) from e
        elif model_args.infer_backend == EngineName.KT:
            try:
                from .kt_engine import KTransformersEngine

                self.engine: BaseEngine = KTransformersEngine(model_args, data_args, finetuning_args, generating_args)
            except ImportError as e:
                raise ImportError(
                    "KTransformers not install, you may need to run `pip install ktransformers`\n"
                    "or try to use HuggingFace backend: --infer_backend huggingface"
                ) from e
        else:
            raise NotImplementedError(f"Unknown backend: {model_args.infer_backend}")

        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=_start_background_loop, args=(self._loop,), daemon=True)
        self._thread.start()