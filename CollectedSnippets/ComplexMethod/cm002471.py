def __init__(
        self,
        model: PreTrainedModel | nn.Module | None = None,
        args: TrainingArguments | None = None,
        data_collator: DataCollator | None = None,
        train_dataset: "Dataset | IterableDataset | datasets.Dataset | None" = None,
        eval_dataset: "Dataset | dict[str, Dataset] | datasets.Dataset | None" = None,
        processing_class: PreTrainedTokenizerBase
        | BaseImageProcessor
        | FeatureExtractionMixin
        | ProcessorMixin
        | None = None,
        model_init: Callable[..., PreTrainedModel] | None = None,
        compute_loss_func: Callable | None = None,
        compute_metrics: Callable[[EvalPrediction], dict] | None = None,
        callbacks: list[TrainerCallback] | None = None,
        optimizers: tuple[torch.optim.Optimizer | None, torch.optim.lr_scheduler.LambdaLR | None] = (None, None),
        optimizer_cls_and_kwargs: tuple[type[torch.optim.Optimizer], dict[str, Any]] | None = None,
        preprocess_logits_for_metrics: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] | None = None,
    ):
        # Init flow:
        #   1. Args & seed               – defaults, determinism
        #   2. Accelerator & logging     – accelerator, memory tracker, log level, device setup
        #   3. Model resolution          – model / model_init, Liger Kernel, quantization checks
        #   4. Distributed strategy      – model-parallel, FSDP, SageMaker MP flags
        #   5. Device placement          – move model to device, model wrapping
        #   6. Model introspection       – loss kwargs, label names, label smoother
        #   7. Store init arguments      – data, callables, optimizer, scheduler, validation
        #   8. Callbacks                 – reporting integrations, JIT checkpoint, progress bar
        #   9. Hub & output              – repo init, output directory
        #  10. Training state            – TrainerState, TrainerControl, internal bookkeeping
        #  11. Finalize                  – use_cache, XLA FSDPv2 mesh, memory tracker stop

        # ---- 1. Args & seed --------------------------------------------------------
        if args is None:
            output_dir = "tmp_trainer"
            logger.info(f"No `TrainingArguments` passed, using `output_dir={output_dir}`.")
            args = TrainingArguments(output_dir=output_dir)
        self.args = args
        # Seed must be set before instantiating the model when using model_init
        enable_full_determinism(self.args.seed) if self.args.full_determinism else set_seed(self.args.seed)

        # ---- 2. Accelerator & logging ----------------------------------------------
        # `create_accelerator_and_postprocess` reads self.model and self.args,
        # and may set self.deepspeed — store temporary refs before calling it.
        self.deepspeed = None
        self.model = model
        self.create_accelerator_and_postprocess()

        self._memory_tracker = TrainerMemoryTracker(self.args.skip_memory_metrics)
        self._memory_tracker.start()

        log_level = args.get_process_log_level()
        logging.set_verbosity(log_level)

        args._setup_devices  # force device and distributed setup init explicitly

        # ---- 3. Model resolution ----------------------------------------------------
        if model is None:
            if model_init is not None:
                self.model_init = model_init
                model = self.call_model_init()
            else:
                raise RuntimeError("`Trainer` requires either a `model` or `model_init` argument")
        else:
            if model_init is not None:
                raise ValueError("`Trainer` requires either a `model` or `model_init` argument, but not both.")
            self.model_init = model_init

        if model.__class__.__name__ in MODEL_MAPPING_NAMES:
            raise ValueError(
                f"The model you have picked ({model.__class__.__name__}) cannot be used as is for training: it only "
                "computes hidden states and does not accept any labels. You should choose a model with a head "
                "suitable for your task like any of the `AutoModelForXxx` listed at "
                "https://huggingface.co/docs/transformers/model_doc/auto"
            )

        validate_quantization_for_training(model)

        # ---- 4. Distributed strategy ------------------------------------------------
        self.is_model_parallel = False
        if getattr(model, "hf_device_map", None) is not None:
            devices = [device for device in set(model.hf_device_map.values()) if device not in ["cpu", "disk"]]
            if len(devices) > 1:
                self.is_model_parallel = True
            elif len(devices) == 1:
                self.is_model_parallel = self.args.device != torch.device(devices[0])

        self.is_fsdp_xla_enabled = args.fsdp_config["xla"]
        if len(args.fsdp) > 0:
            if self.is_deepspeed_enabled:
                raise ValueError(
                    "Using --fsdp xxx together with --deepspeed is not possible, deactivate one of those flags."
                )
            if not args.fsdp_config["xla"] and args.parallel_mode != ParallelMode.DISTRIBUTED:
                raise ValueError("Using fsdp only works in distributed training.")

        # Postpone switching model to cuda when MP, DeepSpeed, full bf16/fp16 eval, or FSDP
        if args.place_model_on_device is not None:
            self.place_model_on_device = args.place_model_on_device
        elif (
            self.is_model_parallel
            or self.is_deepspeed_enabled
            or (args.fp16_full_eval or args.bf16_full_eval)
            or self.is_fsdp_xla_enabled
            or self.is_fsdp_enabled
            or is_sagemaker_mp_enabled()
        ):
            self.place_model_on_device = False
        else:
            self.place_model_on_device = True

        # ---- 5. Device placement ----------------------------------------------------
        # Bnb Quantized models don't support `.to` operation.
        if (
            self.place_model_on_device
            and getattr(model, "quantization_method", None) != QuantizationMethod.BITS_AND_BYTES
        ):
            self._move_model_to_device(model, args.device)

        # Force n_gpu to 1 to avoid DataParallel as MP will manage the GPUs
        if self.is_model_parallel:
            self.args._n_gpu = 1

        # `self.model is self.model_wrapped` is used later to check if it's wrapped
        self.model_wrapped = model
        self.model = model

        # ---- 6. Model introspection -------------------------------------------------
        unwrapped_model = unwrap_peft_model(self.accelerator.unwrap_model(model))

        if hasattr(unwrapped_model, "accepts_loss_kwargs"):
            self.model_accepts_loss_kwargs = unwrapped_model.accepts_loss_kwargs
        else:
            forward_params = inspect.signature(unwrapped_model.forward).parameters
            self.model_accepts_loss_kwargs = any(
                k.kind == inspect.Parameter.VAR_KEYWORD for k in forward_params.values()
            )

        # Sequence Parallelism computes its own good_tokens count
        pc = getattr(self.accelerator, "parallelism_config", None)
        if pc is not None and pc.sp_backend == "deepspeed" and pc.sp_enabled:
            self.model_accepts_loss_kwargs = False

        model_to_inspect = unwrap_peft_model(self.model)
        default_label_names = find_labels(model_to_inspect.__class__)
        self.label_names = default_label_names if self.args.label_names is None else self.args.label_names
        self.can_return_loss = can_return_loss(model_to_inspect.__class__)

        if self.args.label_smoothing_factor != 0:
            if getattr(self.model.config, "problem_type", None) == "multi_label_classification":
                warnings.warn(
                    "Label smoothing is not compatible with multi-label classification. "
                    "Disabling label smoothing for this training run.",
                    UserWarning,
                )
                self.label_smoother = None
            else:
                self.label_smoother = LabelSmoother(epsilon=self.args.label_smoothing_factor)
        else:
            self.label_smoother = None

        # ---- 7. Store init arguments ------------------------------------------------
        # Data
        default_collator = (
            DataCollatorWithPadding(processing_class)
            if processing_class is not None
            and isinstance(processing_class, (PreTrainedTokenizerBase, SequenceFeatureExtractor))
            else default_data_collator
        )
        self.data_collator = data_collator if data_collator is not None else default_collator
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.processing_class = processing_class
        self.neftune_noise_alpha = args.neftune_noise_alpha

        # Callables
        self.compute_loss_func = compute_loss_func
        self.compute_metrics = compute_metrics
        self.preprocess_logits_for_metrics = preprocess_logits_for_metrics

        # Optimizer & scheduler
        self.optimizer, self.lr_scheduler = optimizers
        self.optimizer_cls_and_kwargs = optimizer_cls_and_kwargs

        self._validate_args()

        # ---- 8. Callbacks -----------------------------------------------------------
        default_callbacks = DEFAULT_CALLBACKS + get_reporting_integration_callbacks(self.args.report_to)

        if self.args.enable_jit_checkpoint:
            from .trainer_jit_checkpoint import JITCheckpointCallback

            jit_callback = JITCheckpointCallback()
            default_callbacks = default_callbacks + [jit_callback]
            jit_callback.set_trainer(self)

        callbacks = default_callbacks if callbacks is None else default_callbacks + callbacks
        self.callback_handler = CallbackHandler(
            callbacks, self.model, self.processing_class, self.optimizer, self.lr_scheduler
        )
        self.add_callback(PrinterCallback if self.args.disable_tqdm else DEFAULT_PROGRESS_CALLBACK)

        # ---- 9. Hub & output ---------------------------------------------------------
        self.hub_model_id = None  # Set by init_hf_repo() when push_to_hub is enabled
        if self.args.push_to_hub:
            self.init_hf_repo()
        if self.args.should_save:
            os.makedirs(self.args.output_dir, exist_ok=True)

        # ---- 10. Training state -----------------------------------------------------
        self.control = TrainerControl()
        self.state = TrainerState(
            is_local_process_zero=self.is_local_process_zero(),
            is_world_process_zero=self.is_world_process_zero(),
            stateful_callbacks=[
                cb for cb in self.callback_handler.callbacks + [self.control] if isinstance(cb, ExportableState)
            ],
        )
        self.is_in_train = False  # True between train() entry and exit
        self.hp_name = None  # Set by hyperparameter_search() to label the trial
        self.hp_search_backend = None  # Set by hyperparameter_search() (optuna / ray / wandb)
        # Per-process FLOP counter; accumulated into self.state.total_flos then reset
        self.current_flos = 0
        # Set True by _setup_loggers() on first call to self.log()
        self._loggers_initialized = False
        # Lazily filled by _set_signature_columns_if_needed(); caches model.forward param names
        self._signature_columns = None
        # Effective batch size; may be reduced by find_executable_batch_size
        self._train_batch_size = args.train_batch_size
        # Guards one-time LR scheduler creation in create_optimizer_and_scheduler
        self._created_lr_scheduler = False

        self.control = self.callback_handler.on_init_end(self.args, self.state, self.control)

        # ---- 11. Finalize -----------------------------------------------------------
        if getattr(self.model, "config", None) is not None:
            self.model.config.use_cache = self.args.use_cache

        self.is_fsdp_xla_v2_enabled = args.fsdp_config.get("xla_fsdp_v2", False)
        if self.is_fsdp_xla_v2_enabled:
            if not IS_XLA_FSDPV2_POST_2_2:
                raise ValueError("FSDPv2 requires `torch_xla` 2.2 or higher.")
            num_devices = xr.global_runtime_device_count()
            xs.set_global_mesh(xs.Mesh(np.array(range(num_devices)), (num_devices, 1), axis_names=("fsdp", "tensor")))
        self.is_fsdp_xla_v1_enabled = self.is_fsdp_xla_enabled and not self.is_fsdp_xla_v2_enabled

        self._memory_tracker.stop_and_update_metrics()