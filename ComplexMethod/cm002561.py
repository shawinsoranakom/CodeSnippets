def __post_init__(self):
        # ── 1. Defaults & Normalization ──
        if self.output_dir is None:
            self.output_dir = "trainer_output"
            logger.info(
                "No output directory specified, defaulting to 'trainer_output'. "
                "To change this behavior, specify --output_dir when creating TrainingArguments."
            )

        # Parse JSON string dict args from CLI (e.g., '{"key": "value"}').
        # Only parses strings starting with '{'; other strings are treated as file paths.
        for valid_field in self._VALID_DICT_FIELDS:
            passed_value = getattr(self, valid_field)
            if isinstance(passed_value, str) and passed_value.startswith("{"):
                loaded_dict = json.loads(passed_value)
                loaded_dict = _convert_str_dict(loaded_dict)
                setattr(self, valid_field, loaded_dict)

        # Expand ~ in paths so os.makedirs works correctly (#10628)
        if self.output_dir is not None:
            self.output_dir = os.path.expanduser(self.output_dir)

        if self.disable_tqdm is None:
            self.disable_tqdm = logger.getEffectiveLevel() > logging.WARN

        if self.warmup_ratio is not None:
            logger.warning("warmup_ratio is deprecated and will be removed in v5.2. Use `warmup_steps` instead.")
            self.warmup_steps = self.warmup_ratio

        if self.logging_dir is not None:
            logger.warning(
                "`logging_dir` is deprecated and will be removed in v5.2. Please set `TENSORBOARD_LOGGING_DIR` instead."
            )

        if isinstance(self.include_num_input_tokens_seen, bool):
            self.include_num_input_tokens_seen = "all" if self.include_num_input_tokens_seen else "no"

        # ── 2. Enum / Type Conversions ──
        self.eval_strategy = IntervalStrategy(self.eval_strategy)
        self.logging_strategy = IntervalStrategy(self.logging_strategy)
        self.save_strategy = SaveStrategy(self.save_strategy)
        self.hub_strategy = HubStrategy(self.hub_strategy)
        self.lr_scheduler_type = SchedulerType(self.lr_scheduler_type)
        self.optim = OptimizerNames(self.optim)

        if isinstance(self.debug, str):
            self.debug = [DebugOption(s) for s in self.debug.split()]
        elif self.debug is None:
            self.debug = []

        # ── 3. Auto-derived Values ──
        if self.do_eval is False and self.eval_strategy != IntervalStrategy.NO:
            self.do_eval = True

        # Fall back to logging_steps if eval_steps is unset
        if self.eval_strategy == IntervalStrategy.STEPS and (self.eval_steps is None or self.eval_steps == 0):
            if self.logging_steps > 0:
                logger.info(f"using `logging_steps` to initialize `eval_steps` to {self.logging_steps}")
                self.eval_steps = self.logging_steps
            else:
                raise ValueError(
                    f"evaluation strategy {self.eval_strategy} requires either non-zero --eval_steps or"
                    " --logging_steps"
                )

        if (
            self.load_best_model_at_end
            or self.lr_scheduler_type == SchedulerType.REDUCE_ON_PLATEAU
            or self.lr_scheduler_type == SchedulerType.GREEDY
        ) and self.metric_for_best_model is None:
            self.metric_for_best_model = "loss"
        if self.greater_is_better is None and self.metric_for_best_model is not None:
            self.greater_is_better = not self.metric_for_best_model.endswith("loss")

        if self.report_to == "all" or self.report_to == ["all"]:
            from .integrations import get_available_reporting_integrations

            self.report_to = get_available_reporting_integrations()
        elif self.report_to == "none" or self.report_to == ["none"]:
            self.report_to = []
        elif not isinstance(self.report_to, list):
            self.report_to = [self.report_to]

        # Auto-enable Kubeflow integration when running inside a Kubeflow TrainJob
        from .integrations import is_kubeflow_available

        if is_kubeflow_available() and "kubeflow" not in self.report_to:
            self.report_to = list(self.report_to) + ["kubeflow"]

        # ── 4. Validation ──
        self._validate_args()

        # ── 5. Mixed Precision ──
        # Read from env first; DeepSpeed may override this later
        self.mixed_precision = os.environ.get("ACCELERATE_MIXED_PRECISION", "no")
        if self.fp16:
            self.mixed_precision = "fp16"
        elif self.bf16:
            self.mixed_precision = "bf16"

        # ── 6. Torch Compile ──
        if (self.torch_compile_mode is not None or self.torch_compile_backend is not None) and not self.torch_compile:
            self.torch_compile = True
        if self.torch_compile and self.torch_compile_backend is None:
            if not self.use_cpu and is_torch_hpu_available():
                self.torch_compile_backend = "hpu_backend"
            else:
                self.torch_compile_backend = "inductor"

        if self.torch_compile:
            # TODO: remove env var fallback once minimum accelerate >= 1.2.0
            if not is_accelerate_available("1.2.0"):
                os.environ["ACCELERATE_DYNAMO_BACKEND"] = self.torch_compile_backend
                if self.torch_compile_mode is not None:
                    os.environ["ACCELERATE_DYNAMO_MODE"] = self.torch_compile_mode

        # ── 7. Accelerator Config (must come before self.device) ──
        if is_accelerate_available():
            if not isinstance(self.accelerator_config, AcceleratorConfig):
                if self.accelerator_config is None:
                    self.accelerator_config = AcceleratorConfig()
                elif isinstance(self.accelerator_config, dict):
                    self.accelerator_config = AcceleratorConfig(**self.accelerator_config)
                # Reject uninstantiated class (e.g. AcceleratorConfig instead of AcceleratorConfig())
                elif isinstance(self.accelerator_config, type):
                    raise NotImplementedError(
                        "Tried passing in a callable to `accelerator_config`, but this is not supported. "
                        "Please pass in a fully constructed `AcceleratorConfig` object instead."
                    )
                else:
                    self.accelerator_config = AcceleratorConfig.from_json_file(self.accelerator_config)
            if self.accelerator_config.split_batches:
                logger.info(
                    "Using `split_batches=True` in `accelerator_config` will override the `per_device_train_batch_size` "
                    "Batches will be split across all processes equally when using `split_batches=True`."
                )

        # ── 8. Device Init ──
        if is_torch_available():
            self.device

        # ── 9. TF32 ──
        if is_torch_available() and self.torch_compile:
            if is_torch_tf32_available():
                if self.tf32 is None and not self.fp16 or self.bf16:
                    device_str = "MUSA" if is_torch_musa_available() else "CUDA"
                    logger.info(
                        f"Setting TF32 in {device_str} backends to speedup torch compile, you won't see any improvement"
                        " otherwise."
                    )
                    enable_tf32(True)
            else:
                logger.warning(
                    "The speedups for torchdynamo mostly come with GPU Ampere or higher and which is not detected here."
                )
        if is_torch_available() and self.tf32 is not None:
            if self.tf32:
                if is_torch_tf32_available():
                    enable_tf32(True)
                else:
                    raise ValueError("--tf32 requires Ampere or a newer GPU arch, cuda>=11 and torch>=1.7")
            else:
                if is_torch_tf32_available():
                    enable_tf32(False)
                # TF32 not available, nothing to disable

        # ── 10. Hardware Overrides ──
        if self.use_cpu:
            self.dataloader_pin_memory = False

        # ── 11. FSDP ──
        # Store args only (not the plugin itself) to avoid pickle issues
        self.fsdp_plugin_args = self._process_fsdp_args()

        # ── 12. DeepSpeed (must be last) ──
        self.deepspeed_plugin = None
        if self.deepspeed:
            from transformers.integrations.deepspeed import HfTrainerDeepSpeedConfig

            # Leave self.deepspeed unmodified; users may rely on the original value
            self.hf_deepspeed_config = HfTrainerDeepSpeedConfig(self.deepspeed)
            self.hf_deepspeed_config.trainer_config_process(self)

            from accelerate.utils import DeepSpeedPlugin

            self.deepspeed_plugin = DeepSpeedPlugin(hf_ds_config=self.hf_deepspeed_config)
        elif strtobool(os.environ.get("ACCELERATE_USE_DEEPSPEED", "false")):
            from accelerate.utils import DeepSpeedPlugin

            self.deepspeed_plugin = DeepSpeedPlugin()
            self.deepspeed_plugin.set_mixed_precision(self.mixed_precision)
            self.deepspeed_plugin.set_deepspeed_weakref()