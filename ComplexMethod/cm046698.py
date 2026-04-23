def start_training(self, job_id: str, **kwargs) -> bool:
        """Spawn a subprocess to run the full training pipeline.

        All kwargs are serialized into a config dict and sent to the worker.
        Returns True if the subprocess was started successfully.
        """
        with self._lock:
            if self._proc is not None and self._proc.is_alive():
                logger.warning("Training subprocess already running")
                return False

        # Join prior pump thread — refuse to start if it won't die
        if self._pump_thread is not None and self._pump_thread.is_alive():
            self._pump_thread.join(timeout = 5.0)
            if self._pump_thread.is_alive():
                logger.warning(
                    "Previous pump thread did not exit within 5s — refusing to start"
                )
                return False
        self._pump_thread = None

        # Build config dict for the subprocess
        config = {
            "model_name": kwargs["model_name"],
            "training_type": kwargs.get("training_type", "LoRA/QLoRA"),
            "hf_token": kwargs.get("hf_token", ""),
            "load_in_4bit": kwargs.get("load_in_4bit", True),
            "max_seq_length": kwargs.get("max_seq_length", 2048),
            "hf_dataset": kwargs.get("hf_dataset", ""),
            "local_datasets": kwargs.get("local_datasets"),
            "local_eval_datasets": kwargs.get("local_eval_datasets"),
            "format_type": kwargs.get("format_type", ""),
            "subset": kwargs.get("subset"),
            "train_split": kwargs.get("train_split", "train"),
            "eval_split": kwargs.get("eval_split"),
            "eval_steps": kwargs.get("eval_steps", 0.00),
            "dataset_slice_start": kwargs.get("dataset_slice_start"),
            "dataset_slice_end": kwargs.get("dataset_slice_end"),
            "custom_format_mapping": kwargs.get("custom_format_mapping"),
            "is_dataset_image": kwargs.get("is_dataset_image", False),
            "is_dataset_audio": kwargs.get("is_dataset_audio", False),
            "is_embedding": kwargs.get("is_embedding", False),
            "num_epochs": kwargs.get("num_epochs", 3),
            "learning_rate": kwargs.get("learning_rate", "2e-4"),
            "batch_size": kwargs.get("batch_size", 2),
            "gradient_accumulation_steps": kwargs.get("gradient_accumulation_steps", 4),
            "warmup_steps": kwargs.get("warmup_steps"),
            "warmup_ratio": kwargs.get("warmup_ratio"),
            "max_steps": kwargs.get("max_steps", 0),
            "save_steps": kwargs.get("save_steps", 0),
            "weight_decay": kwargs.get("weight_decay", 0.001),
            "random_seed": kwargs.get("random_seed", 3407),
            "packing": kwargs.get("packing", False),
            "optim": kwargs.get("optim", "adamw_8bit"),
            "lr_scheduler_type": kwargs.get("lr_scheduler_type", "linear"),
            "use_lora": kwargs.get("use_lora", True),
            "lora_r": kwargs.get("lora_r", 16),
            "lora_alpha": kwargs.get("lora_alpha", 16),
            "lora_dropout": kwargs.get("lora_dropout", 0.0),
            "target_modules": kwargs.get("target_modules"),
            "gradient_checkpointing": kwargs.get("gradient_checkpointing", "unsloth"),
            "use_rslora": kwargs.get("use_rslora", False),
            "use_loftq": kwargs.get("use_loftq", False),
            "train_on_completions": kwargs.get("train_on_completions", False),
            "finetune_vision_layers": kwargs.get("finetune_vision_layers", True),
            "finetune_language_layers": kwargs.get("finetune_language_layers", True),
            "finetune_attention_modules": kwargs.get(
                "finetune_attention_modules", True
            ),
            "finetune_mlp_modules": kwargs.get("finetune_mlp_modules", True),
            "enable_wandb": kwargs.get("enable_wandb", False),
            "wandb_token": kwargs.get("wandb_token"),
            "wandb_project": kwargs.get("wandb_project", "unsloth-training"),
            "enable_tensorboard": kwargs.get("enable_tensorboard", False),
            "tensorboard_dir": kwargs.get("tensorboard_dir", "runs"),
            "trust_remote_code": kwargs.get("trust_remote_code", False),
            "gpu_ids": kwargs.get("gpu_ids"),
        }

        # Derive load_in_4bit from training_type
        if config["training_type"] != "LoRA/QLoRA":
            config["load_in_4bit"] = False

        # Spawn subprocess — use locals so state is untouched on failure
        resolved_gpu_ids, gpu_selection = prepare_gpu_selection(
            kwargs.get("gpu_ids"),
            model_name = config["model_name"],
            hf_token = config["hf_token"] or None,
            training_type = config["training_type"],
            load_in_4bit = config["load_in_4bit"],
            batch_size = config.get("batch_size", 4),
            max_seq_length = config.get("max_seq_length", 2048),
            lora_rank = config.get("lora_r", 16),
            target_modules = config.get("target_modules"),
            gradient_checkpointing = config.get("gradient_checkpointing", "unsloth"),
            optimizer = config.get("optim", "adamw_8bit"),
        )
        config["resolved_gpu_ids"] = resolved_gpu_ids
        config["gpu_selection"] = gpu_selection

        from .worker import run_training_process

        event_queue = _CTX.Queue()
        stop_queue = _CTX.Queue()

        proc = _CTX.Process(
            target = run_training_process,
            kwargs = {
                "event_queue": event_queue,
                "stop_queue": stop_queue,
                "config": config,
            },
            daemon = True,
        )
        try:
            proc.start()
        except Exception:
            logger.error("Failed to start training subprocess", exc_info = True)
            return False

        logger.info("Training subprocess started (pid=%s)", proc.pid)

        # Reset state — safe because old pump thread is confirmed dead
        # and proc.start() succeeded
        self.current_job_id = job_id
        self._should_stop = False
        self._cancel_requested = False
        self._progress = TrainingProgress(
            is_training = True, status_message = "Initializing training..."
        )
        self.loss_history.clear()
        self.lr_history.clear()
        self.step_history.clear()
        self.grad_norm_history.clear()
        self.grad_norm_step_history.clear()
        self.eval_loss_history.clear()
        self.eval_step_history.clear()
        self.eval_enabled = False
        self._output_dir = None
        self._metric_buffer.clear()
        self._run_finalized = False
        self._db_run_created = False
        self._db_total_steps_set = False
        self._db_config = {
            k: v for k, v in config.items() if k not in {"hf_token", "wandb_token"}
        }
        self._db_started_at = datetime.now(timezone.utc).isoformat()

        # Assign subprocess handles after state reset
        self._event_queue = event_queue
        self._stop_queue = stop_queue
        self._proc = proc

        # Eagerly create DB run row so the run appears in history during model loading
        self._ensure_db_run_created()

        # Start event pump thread
        self._pump_thread = threading.Thread(target = self._pump_loop, daemon = True)
        self._pump_thread.start()

        return True