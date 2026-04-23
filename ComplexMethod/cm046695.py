def run_training_process(
    *,
    event_queue: Any,
    stop_queue: Any,
    config: dict,
) -> None:
    """Subprocess entrypoint. Fresh Python — no stale module state.

    Args:
        event_queue: mp.Queue for sending progress/status/error events to parent.
        stop_queue: mp.Queue for receiving stop commands from parent.
        config: Training configuration dict with all parameters.
    """
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["PYTHONWARNINGS"] = (
        "ignore"  # Suppress warnings at C-level before imports
    )

    import warnings
    from loggers.config import LogConfig

    if os.getenv("ENVIRONMENT_TYPE", "production") == "production":
        warnings.filterwarnings("ignore")

    LogConfig.setup_logging(
        service_name = "unsloth-studio-training-worker",
        env = os.getenv("ENVIRONMENT_TYPE", "production"),
    )

    apply_gpu_ids(config.get("resolved_gpu_ids"))

    model_name = config["model_name"]

    # ── 1. Activate correct transformers version BEFORE any ML imports ──
    try:
        _activate_transformers_version(model_name)
    except Exception as exc:
        event_queue.put(
            {
                "type": "error",
                "error": f"Failed to activate transformers version: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── 1a. Auto-enable trust_remote_code for NemotronH/Nano models ──
    # NemotronH has config parsing bugs in transformers that require
    # trust_remote_code=True as a workaround. Other transformers 5.x models
    # (Qwen3.5, Gemma 4, etc.) are native and do NOT need it — enabling it
    # bypasses the compiler (disabling fused CE).
    # NOTE: Must NOT match Llama-Nemotron (standard Llama architecture).
    _NEMOTRON_TRUST_SUBSTRINGS = ("nemotron_h", "nemotron-h", "nemotron-3-nano")
    _lowered = model_name.lower()
    if (
        any(sub in _lowered for sub in _NEMOTRON_TRUST_SUBSTRINGS)
        and (_lowered.startswith("unsloth/") or _lowered.startswith("nvidia/"))
        and not config.get("trust_remote_code", False)
    ):
        config["trust_remote_code"] = True
        logger.info(
            "Auto-enabled trust_remote_code for Nemotron model: %s",
            model_name,
        )

    # ── 1b. Set up causal-conv1d first, then install mamba-ssm if needed ──
    try:
        _ensure_causal_conv1d_fast_path(event_queue, model_name)
        _ensure_mamba_ssm(event_queue, model_name)
        _ensure_flash_attn_for_long_context(
            event_queue,
            int(config.get("max_seq_length", 2048)),
        )
    except Exception as exc:
        event_queue.put(
            {
                "type": "error",
                "error": (
                    f"Please choose another model to train, since "
                    f"causal-conv1d / mamba-ssm failed to install "
                    f"with error: {exc}"
                ),
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── 1c. Set fork start method so dataset.map() can multiprocess ──
    # The parent launched us via spawn (clean process), but the compiled
    # SFTTrainer checks get_start_method() and disables num_proc if not "fork".
    # Linux only: fork is the default start method and is safe here (no CUDA
    # context exists yet). macOS defaults to spawn since Python 3.8 because
    # fork is unsafe with macOS frameworks (Metal/MPS, CoreFoundation) --
    # do NOT override on macOS. Windows has no fork at all.
    if sys.platform == "linux":
        import multiprocessing as _mp

        try:
            _mp.set_start_method("fork", force = True)
        except RuntimeError:
            pass  # Already set

    # ── 1c. On Windows, check Triton availability (must be before import torch) ──
    if sys.platform == "win32":
        try:
            import triton  # noqa: F401

            logger.info("Triton available — torch.compile enabled")
        except ImportError:
            os.environ["TORCHDYNAMO_DISABLE"] = "1"
            logger.warning(
                "Triton not found on Windows — torch.compile disabled. "
                'Install for better performance: pip install "triton-windows<3.7"'
            )

    # ── 2. Now import ML libraries (fresh in this clean process) ──
    try:
        _send_status(event_queue, "Importing Unsloth...")

        backend_path = str(Path(__file__).resolve().parent.parent.parent)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from core.training.trainer import UnslothTrainer, TrainingProgress
        from utils.paths import (
            ensure_dir,
            resolve_output_dir,
            resolve_tensorboard_dir,
            datasets_root,
        )

        import transformers

        logger.info("Subprocess loaded transformers %s", transformers.__version__)
    except Exception as exc:
        event_queue.put(
            {
                "type": "error",
                "error": f"Failed to import ML libraries: {exc}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── 2b. EMBEDDING MODEL FAST-PATH ──
    # Embedding models use a completely different pipeline (FastSentenceTransformer
    # + SentenceTransformerTrainer + MultipleNegativesRankingLoss) so we branch
    # early and handle the entire flow in a self-contained function.
    if config.get("is_embedding", False):
        try:
            _run_embedding_training(event_queue, stop_queue, config)
        except Exception as exc:
            event_queue.put(
                {
                    "type": "error",
                    "error": str(exc),
                    "stack": traceback.format_exc(limit = 20),
                    "ts": time.time(),
                }
            )
        return

    # ── 3. Create a fresh trainer instance ──
    trainer = UnslothTrainer()

    # Wire up progress callback → event_queue
    def _on_progress(progress: TrainingProgress):
        has_train_loss = progress.step > 0 and progress.loss is not None
        has_eval_loss = progress.eval_loss is not None
        if has_train_loss or has_eval_loss:
            event_queue.put(
                {
                    "type": "progress",
                    "step": progress.step,
                    "epoch": progress.epoch,
                    "loss": progress.loss,
                    "learning_rate": progress.learning_rate,
                    "total_steps": progress.total_steps,
                    "elapsed_seconds": progress.elapsed_seconds,
                    "eta_seconds": progress.eta_seconds,
                    "grad_norm": progress.grad_norm,
                    "num_tokens": progress.num_tokens,
                    "eval_loss": progress.eval_loss,
                    "status_message": progress.status_message,
                    "ts": time.time(),
                }
            )
        if progress.status_message:
            _send_status(event_queue, progress.status_message)

    trainer.add_progress_callback(_on_progress)

    # Wire up stop_queue polling to trainer.should_stop
    import threading
    import queue as _queue

    def _poll_stop():
        while True:
            try:
                msg = stop_queue.get(timeout = 1.0)
                if msg and msg.get("type") == "stop":
                    save = msg.get("save", True)
                    trainer.should_stop = True
                    trainer.save_on_stop = save
                    logger.info("Stop signal received (save=%s)", save)
                    return
            except _queue.Empty:
                continue
            except (EOFError, OSError):
                return

    stop_thread = threading.Thread(target = _poll_stop, daemon = True)
    stop_thread.start()

    # ── 4. Execute the training pipeline ──
    # Order: detect → dataset → model → prepare → train
    # Dataset processing (including LLM-assisted detection) runs BEFORE model
    # loading so both never occupy VRAM at the same time.
    try:
        hf_token = config.get("hf_token", "")
        hf_token = hf_token if hf_token and hf_token.strip() else None

        # ── 4a. Lightweight detection + tokenizer (no VRAM) ──
        _send_status(event_queue, "Detecting model type...")
        trainer.pre_detect_and_load_tokenizer(
            model_name = model_name,
            max_seq_length = config["max_seq_length"],
            hf_token = hf_token,
            is_dataset_image = config.get("is_dataset_image", False),
            is_dataset_audio = config.get("is_dataset_audio", False),
            trust_remote_code = config.get("trust_remote_code", False),
        )
        if trainer.should_stop:
            event_queue.put({"type": "complete", "output_dir": None, "ts": time.time()})
            return

        # ── 4b. Load and format dataset (LLM helper may use VRAM briefly) ──
        _send_status(event_queue, "Loading and formatting dataset...")
        hf_dataset = config.get("hf_dataset", "")
        dataset_result = trainer.load_and_format_dataset(
            dataset_source = hf_dataset if hf_dataset and hf_dataset.strip() else None,
            format_type = config.get("format_type", ""),
            local_datasets = config.get("local_datasets") or None,
            local_eval_datasets = config.get("local_eval_datasets") or None,
            custom_format_mapping = config.get("custom_format_mapping"),
            subset = config.get("subset"),
            train_split = config.get("train_split", "train"),
            eval_split = config.get("eval_split"),
            eval_steps = config.get("eval_steps", 0.00),
            dataset_slice_start = config.get("dataset_slice_start"),
            dataset_slice_end = config.get("dataset_slice_end"),
        )

        if isinstance(dataset_result, tuple):
            dataset, eval_dataset = dataset_result
        else:
            dataset = dataset_result
            eval_dataset = None

        # [DEBUG] Print first sample before model is loaded
        # dataset is a dict {"dataset": <Dataset>, "detected_format": ..., ...}
        # or a raw Dataset for audio paths
        # try:
        #     ds = dataset["dataset"] if isinstance(dataset, dict) else dataset
        #     print(
        #         f"\n[DEBUG] Dataset loaded BEFORE model. type={type(ds).__name__}, len={len(ds)}",
        #         flush = True,
        #     )
        #     print(f"[DEBUG] Columns: {ds.column_names}", flush = True)
        #     sample = ds[0]
        #     preview = {k: str(v)[:300] for k, v in sample.items()}
        #     print(f"[DEBUG] First sample: {preview}\n", flush = True)
        # except Exception as e:
        #     print(
        #         f"[DEBUG] Could not preview first sample: {type(e).__name__}: {e}",
        #         flush = True,
        #     )

        # Disable eval if eval_steps <= 0
        eval_steps = config.get("eval_steps", 0.00)
        if eval_steps is not None and float(eval_steps) <= 0:
            eval_dataset = None

        # Tell the parent process that eval is configured so the frontend
        # shows "Waiting for first evaluation step..." instead of "not configured"
        if eval_dataset is not None:
            event_queue.put(
                {
                    "type": "eval_configured",
                    "ts": time.time(),
                }
            )

        if dataset is None or trainer.should_stop:
            if trainer.should_stop:
                event_queue.put(
                    {"type": "complete", "output_dir": None, "ts": time.time()}
                )
            else:
                event_queue.put(
                    {
                        "type": "error",
                        "error": trainer.training_progress.error
                        or "Failed to load dataset",
                        "stack": "",
                        "ts": time.time(),
                    }
                )
            return

        # ── Start tqdm monitor early so it captures download + tokenization bars ──
        import threading as _th

        _tqdm_stop = _th.Event()

        def _monitor_tqdm():
            from tqdm.auto import tqdm as _tqdm_cls

            while not _tqdm_stop.is_set():
                for bar in list(getattr(_tqdm_cls, "_instances", set())):
                    try:
                        n, total = bar.n or 0, bar.total or 0
                        desc = getattr(bar, "desc", "") or ""
                        if total > 0 and n > 0 and desc:
                            pct = min(int(n * 100 / total), 100)
                            _send_status(
                                event_queue, f"{desc.strip()} {pct}% ({n:,}/{total:,})"
                            )
                    except (AttributeError, ReferenceError):
                        pass
                _tqdm_stop.wait(3)

        _tqdm_thread = _th.Thread(target = _monitor_tqdm, daemon = True)
        _tqdm_thread.start()

        training_type = config.get("training_type", "LoRA/QLoRA")
        use_lora = training_type == "LoRA/QLoRA"

        # ── 4c. Load training model (uses VRAM — dataset already formatted) ──
        _send_status(event_queue, "Loading model...")
        success = trainer.load_model(
            model_name = model_name,
            max_seq_length = config["max_seq_length"],
            load_in_4bit = config["load_in_4bit"],
            full_finetuning = not use_lora,
            hf_token = hf_token,
            is_dataset_image = config.get("is_dataset_image", False),
            is_dataset_audio = config.get("is_dataset_audio", False),
            trust_remote_code = config.get("trust_remote_code", False),
            gpu_ids = config.get("resolved_gpu_ids"),
        )
        if not success or trainer.should_stop:
            if trainer.should_stop:
                event_queue.put(
                    {"type": "complete", "output_dir": None, "ts": time.time()}
                )
            else:
                error_msg = trainer.training_progress.error or "Failed to load model"
                event_queue.put(
                    {
                        "type": "error",
                        "error": error_msg,
                        "stack": "",
                        "ts": time.time(),
                    }
                )
            return

        # ── 4d. Prepare model (LoRA or full finetuning) ──
        if use_lora:
            _send_status(event_queue, "Configuring LoRA adapters...")
            success = trainer.prepare_model_for_training(
                use_lora = True,
                finetune_vision_layers = config.get("finetune_vision_layers", True),
                finetune_language_layers = config.get("finetune_language_layers", True),
                finetune_attention_modules = config.get(
                    "finetune_attention_modules", True
                ),
                finetune_mlp_modules = config.get("finetune_mlp_modules", True),
                target_modules = config.get("target_modules"),
                lora_r = config.get("lora_r", 16),
                lora_alpha = config.get("lora_alpha", 16),
                lora_dropout = config.get("lora_dropout", 0.0),
                use_gradient_checkpointing = config.get(
                    "gradient_checkpointing", "unsloth"
                ),
                use_rslora = config.get("use_rslora", False),
                use_loftq = config.get("use_loftq", False),
            )
        else:
            _send_status(event_queue, "Preparing model for full finetuning...")
            success = trainer.prepare_model_for_training(use_lora = False)

        if not success or trainer.should_stop:
            if trainer.should_stop:
                event_queue.put(
                    {"type": "complete", "output_dir": None, "ts": time.time()}
                )
            else:
                event_queue.put(
                    {
                        "type": "error",
                        "error": trainer.training_progress.error
                        or "Failed to prepare model",
                        "stack": "",
                        "ts": time.time(),
                    }
                )
            return

        # Convert learning rate
        try:
            lr_value = float(config.get("learning_rate", "2e-4"))
        except ValueError:
            event_queue.put(
                {
                    "type": "error",
                    "error": f"Invalid learning rate: {config.get('learning_rate')}",
                    "stack": "",
                    "ts": time.time(),
                }
            )
            return

        # Generate output dir
        output_dir = config.get("output_dir")
        if not output_dir:
            output_dir = f"{model_name.replace('/', '_')}_{int(time.time())}"
        output_dir = str(resolve_output_dir(output_dir))
        ensure_dir(Path(output_dir))

        tensorboard_dir = config.get("tensorboard_dir")
        if config.get("enable_tensorboard", False):
            tensorboard_dir = str(resolve_tensorboard_dir(tensorboard_dir))
            ensure_dir(Path(tensorboard_dir))

        # Start training (directly — no inner thread, we ARE the subprocess)
        dataset_display = (
            config.get("hf_dataset", "") or config.get("uploaded_file", "") or ""
        )
        _send_status(
            event_queue,
            f'Training "{model_name}"'
            + (f"\nDataset = {dataset_display}" if dataset_display else ""),
        )
        max_steps = config.get("max_steps", 0)
        save_steps = config.get("save_steps", 0)

        trainer._train_worker(
            dataset,
            output_dir = output_dir,
            num_epochs = config.get("num_epochs", 3),
            learning_rate = lr_value,
            batch_size = config.get("batch_size", 2),
            gradient_accumulation_steps = config.get("gradient_accumulation_steps", 4),
            warmup_steps = config.get("warmup_steps"),
            warmup_ratio = config.get("warmup_ratio"),
            max_steps = max_steps if max_steps and max_steps > 0 else 0,
            save_steps = save_steps if save_steps and save_steps > 0 else 0,
            weight_decay = config.get("weight_decay", 0.001),
            random_seed = config.get("random_seed", 3407),
            packing = config.get("packing", False),
            train_on_completions = config.get("train_on_completions", False),
            enable_wandb = config.get("enable_wandb", False),
            wandb_project = config.get("wandb_project", "unsloth-training"),
            wandb_token = config.get("wandb_token"),
            enable_tensorboard = config.get("enable_tensorboard", False),
            tensorboard_dir = tensorboard_dir,
            eval_dataset = eval_dataset,
            eval_steps = eval_steps,
            max_seq_length = config.get("max_seq_length", 2048),
            optim = config.get("optim", "adamw_8bit"),
            lr_scheduler_type = config.get("lr_scheduler_type", "linear"),
        )

        _tqdm_stop.set()

        # Check final state
        progress = trainer.get_training_progress()
        if progress.error:
            event_queue.put(
                {
                    "type": "error",
                    "error": progress.error,
                    "stack": "",
                    "ts": time.time(),
                }
            )
        else:
            event_queue.put(
                {
                    "type": "complete",
                    "output_dir": output_dir,
                    "status_message": progress.status_message or "Training completed",
                    "ts": time.time(),
                }
            )

    except Exception as exc:
        event_queue.put(
            {
                "type": "error",
                "error": str(exc),
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )