def train(
        self,
        resume_from_checkpoint: str | bool | None = None,
        trial: "optuna.Trial | dict[str, Any] | None" = None,
        ignore_keys_for_eval: list[str] | None = None,
    ) -> TrainOutput:
        """
        Main training entry point.

        Args:
            resume_from_checkpoint (`str` or `bool`, *optional*):
                If a `str`, local path to a saved checkpoint as saved by a previous instance of [`Trainer`]. If a
                `bool` and equals `True`, load the last checkpoint in *args.output_dir* as saved by a previous instance
                of [`Trainer`]. If present, training will resume from the model/optimizer/scheduler states loaded here.
            trial (`optuna.Trial` or `dict[str, Any]`, *optional*):
                The trial run or the hyperparameter dictionary for hyperparameter search.
            ignore_keys_for_eval (`list[str]`, *optional*)
                A list of keys in the output of your model (if it is a dictionary) that should be ignored when
                gathering predictions for evaluation during the training.

        Returns:
            [`~trainer_utils.TrainOutput`]: Object containing the global step count, training loss, and metrics.
        """
        if resume_from_checkpoint is False:
            resume_from_checkpoint = None

        # memory metrics - must set up as early as possible
        self._memory_tracker.start()

        args = self.args

        self.is_in_train = True

        # Model re-init
        if self.model_init is not None:
            # Seed must be set before instantiating the model when using model_init.
            enable_full_determinism(args.seed) if args.full_determinism else set_seed(args.seed)
            self.model = self.call_model_init(trial)
            # Reinitializes optimizer and scheduler
            self.optimizer, self.lr_scheduler = None, None
            if self.place_model_on_device:
                self._move_model_to_device(self.model, args.device)
            self.model_wrapped = self.model

        if self.args.use_liger_kernel:
            apply_liger_kernel(self.model, self.args.liger_kernel_config)

        # When fp16/bf16 full eval is enabled, __init__ skips device placement so that
        # evaluation_loop can cast dtype and move in one step. Move the model now for training.
        if (args.fp16_full_eval or args.bf16_full_eval) and not self.is_model_parallel and self.model_init is None:
            self._move_model_to_device(self.model, args.device)

        # Activate gradient checkpointing if needed
        if args.gradient_checkpointing:
            self.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs=args.gradient_checkpointing_kwargs)

        # If the model uses a tokenizer, it may have a new tokens for fine-tuning purposes.
        if isinstance(self.processing_class, (PreTrainedTokenizerBase, ProcessorMixin)) and hasattr(
            self.model, "config"
        ):
            align_special_tokens(self.model, self.processing_class)

        # Attach NEFTune hooks if necessary
        if self.neftune_noise_alpha is not None:
            self.neftune_hook_handle = activate_neftune(self.model, self.neftune_noise_alpha, self.accelerator)

        # This might change the seed so needs to run first.
        self._hp_search_setup(trial)

        if DebugOption.UNDERFLOW_OVERFLOW in args.debug:
            if args.n_gpu > 1:
                # nn.DataParallel(model) replicates the model, creating new variables and module
                # references registered here no longer work on other gpus, breaking the module
                raise ValueError(
                    "Currently --debug underflow_overflow is not supported under DP. Please use DDP with torchrun"
                )
            else:
                DebugUnderflowOverflow(self.model)

        # Load potential model checkpoint
        if isinstance(resume_from_checkpoint, bool) and resume_from_checkpoint:
            resume_from_checkpoint = get_last_checkpoint(args.output_dir)
            if resume_from_checkpoint is None:
                raise ValueError(f"No valid checkpoint found in output directory ({args.output_dir})")

        if resume_from_checkpoint is not None:
            # Load model checkpoint before accelerator.prepare() for regular models,
            # so that buffers and parameters are on the right device after prepare.
            # Deepspeed/FSDP models are loaded after prepare in _prepare_for_training.
            if not is_sagemaker_mp_enabled() and not self.is_deepspeed_enabled and not self.is_fsdp_enabled:
                self._load_from_checkpoint(resume_from_checkpoint)
            state = TrainerState.load_from_json(os.path.join(resume_from_checkpoint, TRAINER_STATE_NAME))
            if state.train_batch_size is not None and args.auto_find_batch_size:
                # Only restore the checkpoint's train_batch_size when using auto_find_batch_size,
                self._train_batch_size = state.train_batch_size

        inner_training_loop = find_executable_batch_size(
            self._inner_training_loop, self._train_batch_size, args.auto_find_batch_size
        )
        # Disable progress bars when uploading models during checkpoints to avoid polluting stdout
        ctx = suppress_progress_bars() if args.push_to_hub else contextlib.nullcontext()
        with ctx:
            return inner_training_loop(
                args=args,
                resume_from_checkpoint=resume_from_checkpoint,
                trial=trial,
                ignore_keys_for_eval=ignore_keys_for_eval,
            )