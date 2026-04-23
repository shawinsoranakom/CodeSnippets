def _run_embedding_training(event_queue: Any, stop_queue: Any, config: dict) -> None:
    """Self-contained embedding model training pipeline.

    Uses FastSentenceTransformer + SentenceTransformerTrainer +
    MultipleNegativesRankingLoss — completely separate from the
    LLM/VLM/audio paths in UnslothTrainer.

    Mirrors the pattern from the reference embedding notebooks:
      All_MiniLM_L6_v2.py, BGE_M3.py, EmbeddingGemma_300M.py,
      ModernBert.py, Qwen3_Embedding_0_6B.py
    """
    import math
    import queue as _queue
    import threading

    model_name = config["model_name"]
    training_start_time = time.time()

    # ── 1. Import embedding-specific libraries ──
    _send_status(event_queue, "Importing embedding libraries...")
    try:
        from unsloth import FastSentenceTransformer, is_bfloat16_supported
        from sentence_transformers import (
            SentenceTransformerTrainer,
            SentenceTransformerTrainingArguments,
        )
        from sentence_transformers.losses import MultipleNegativesRankingLoss
        from sentence_transformers.training_args import BatchSamplers
        from datasets import load_dataset, Dataset
        from transformers import TrainerCallback
        from utils.paths import datasets_root, resolve_output_dir
    except ImportError as e:
        event_queue.put(
            {
                "type": "error",
                "error": f"Failed to import embedding libraries: {e}. "
                "Ensure 'sentence_transformers' and 'unsloth' are installed.",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── Stop signal handling ──
    _should_stop = False
    _save_on_stop = True

    def _poll_stop():
        nonlocal _should_stop, _save_on_stop
        while True:
            try:
                msg = stop_queue.get(timeout = 1.0)
                if msg and msg.get("type") == "stop":
                    _save_on_stop = msg.get("save", True)
                    _should_stop = True
                    logger.info(
                        "Embedding training: stop signal received (save=%s)",
                        _save_on_stop,
                    )
                    return
            except _queue.Empty:
                continue
            except (EOFError, OSError):
                return

    stop_thread = threading.Thread(target = _poll_stop, daemon = True)
    stop_thread.start()

    # ── 2. Load model ──
    _send_status(event_queue, "Loading embedding model...")
    try:
        hf_token = config.get("hf_token", "")
        hf_token = hf_token if hf_token and hf_token.strip() else None
        max_seq_length = config.get("max_seq_length", 512)
        training_type = config.get("training_type", "LoRA/QLoRA")
        use_lora = training_type == "LoRA/QLoRA"

        model = FastSentenceTransformer.from_pretrained(
            model_name = model_name,
            max_seq_length = max_seq_length,
            full_finetuning = not use_lora,
            token = hf_token,
        )
    except Exception as e:
        event_queue.put(
            {
                "type": "error",
                "error": f"Failed to load embedding model '{model_name}': {e}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    if _should_stop:
        event_queue.put({"type": "complete", "output_dir": None, "ts": time.time()})
        return

    # ── 3. Apply LoRA ──
    if use_lora:
        _send_status(event_queue, "Configuring LoRA adapters (FEATURE_EXTRACTION)...")
        try:
            gradient_checkpointing = config.get("gradient_checkpointing", False)
            # Normalize: "none" or empty → False
            if gradient_checkpointing in ("none", "", None):
                gradient_checkpointing = False

            model = FastSentenceTransformer.get_peft_model(
                model,
                r = config.get("lora_r", 32),
                target_modules = config.get("target_modules")
                or ["q_proj", "k_proj", "v_proj", "o_proj"],
                lora_alpha = config.get("lora_alpha", 64),
                lora_dropout = config.get("lora_dropout", 0.0),
                bias = "none",
                use_gradient_checkpointing = gradient_checkpointing,
                random_state = config.get("random_seed", 3407),
                use_rslora = config.get("use_rslora", False),
                loftq_config = {"loftq_bits": 4, "loftq_iter": 1}
                if config.get("use_loftq")
                else None,
                task_type = "FEATURE_EXTRACTION",
            )
        except Exception as e:
            event_queue.put(
                {
                    "type": "error",
                    "error": f"Failed to configure LoRA for embedding model: {e}",
                    "stack": traceback.format_exc(limit = 20),
                    "ts": time.time(),
                }
            )
            return

    if _should_stop:
        event_queue.put({"type": "complete", "output_dir": None, "ts": time.time()})
        return

    # ── 4. Load dataset ──
    _send_status(event_queue, "Loading dataset...")
    try:
        hf_dataset = config.get("hf_dataset", "")
        local_datasets = config.get("local_datasets") or []
        subset = config.get("subset") or None
        train_split = config.get("train_split", "train") or "train"

        if hf_dataset and hf_dataset.strip():
            hf_token = config.get("hf_token", "")
            hf_token = hf_token if hf_token and hf_token.strip() else None
            dataset = load_dataset(
                hf_dataset.strip(),
                subset,
                split = train_split,
                token = hf_token,
            )
        elif local_datasets:
            # Load from local file(s) — mirrors the non-embedding pipeline's
            # directory handling so recipe outputs (parquet-files/) work.
            all_files: list[str] = []
            for dataset_file in local_datasets:
                file_path = (
                    dataset_file
                    if os.path.isabs(dataset_file)
                    else os.path.join(
                        str(datasets_root()),
                        dataset_file,
                    )
                )
                if os.path.isdir(file_path):
                    file_path_obj = Path(file_path)
                    parquet_dir = (
                        file_path_obj / "parquet-files"
                        if (file_path_obj / "parquet-files").exists()
                        else file_path_obj
                    )
                    parquet_files = sorted(parquet_dir.glob("*.parquet"))
                    if parquet_files:
                        all_files.extend(str(p) for p in parquet_files)
                        continue
                    candidates: list[Path] = []
                    for ext in (".json", ".jsonl", ".csv", ".parquet"):
                        candidates.extend(sorted(file_path_obj.glob(f"*{ext}")))
                    if candidates:
                        all_files.extend(str(c) for c in candidates)
                        continue
                    raise ValueError(
                        f"No supported data files in directory: {file_path_obj}"
                    )
                else:
                    all_files.append(file_path)

            if all_files:
                first_ext = Path(all_files[0]).suffix.lower()
                if first_ext in (".json", ".jsonl"):
                    loader = "json"
                elif first_ext == ".csv":
                    loader = "csv"
                elif first_ext == ".parquet":
                    loader = "parquet"
                else:
                    raise ValueError(
                        f"Unsupported local dataset format: {all_files[0]}"
                    )
                dataset = load_dataset(loader, data_files = all_files, split = "train")
        else:
            event_queue.put(
                {
                    "type": "error",
                    "error": "No dataset specified for embedding training.",
                    "stack": "",
                    "ts": time.time(),
                }
            )
            return

        # Apply dataset slicing if specified
        slice_start = config.get("dataset_slice_start")
        slice_end = config.get("dataset_slice_end")
        if slice_start is not None or slice_end is not None:
            start = slice_start if slice_start is not None else 0
            end = slice_end if slice_end is not None else len(dataset)
            dataset = dataset.select(range(start, min(end + 1, len(dataset))))

        logger.info(f"Embedding dataset loaded: {len(dataset)} samples")
    except Exception as e:
        event_queue.put(
            {
                "type": "error",
                "error": f"Failed to load dataset: {e}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    if _should_stop:
        event_queue.put({"type": "complete", "output_dir": None, "ts": time.time()})
        return

    # ── 5. Create loss function ──
    loss = MultipleNegativesRankingLoss(model)

    # ── 6. Build training arguments ──
    _send_status(event_queue, "Configuring training...")
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

    output_dir = config.get("output_dir")
    if not output_dir:
        output_dir = str(
            resolve_output_dir(f"{model_name.replace('/', '_')}_{int(time.time())}")
        )

    num_epochs = config.get("num_epochs", 2)
    batch_size = config.get("batch_size", 256)
    gradient_accumulation_steps = config.get("gradient_accumulation_steps", 1)
    max_steps_val = config.get("max_steps", 0)
    save_steps_val = config.get("save_steps", 0)
    warmup_ratio = config.get("warmup_ratio", 0.03)
    warmup_steps_val = config.get("warmup_steps")
    log_frequency = config.get("log_frequency", 50)

    # Build args dict
    training_args_kwargs = {
        "output_dir": output_dir,
        "per_device_train_batch_size": batch_size,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "learning_rate": lr_value,
        "fp16": not is_bfloat16_supported(),
        "bf16": is_bfloat16_supported(),
        "logging_steps": 1,
        "report_to": ["wandb"] if config.get("enable_wandb") else "none",
        "lr_scheduler_type": config.get("lr_scheduler_type", "linear"),
        "batch_sampler": BatchSamplers.NO_DUPLICATES,
        "optim": config.get("optim", "adamw_8bit"),
        "weight_decay": config.get("weight_decay", 0.001),
        "seed": config.get("random_seed", 3407),
    }

    # max_steps vs epochs
    if max_steps_val and max_steps_val > 0:
        training_args_kwargs["max_steps"] = max_steps_val
    else:
        training_args_kwargs["num_train_epochs"] = num_epochs if num_epochs > 0 else 2

    # warmup: prefer warmup_ratio (standard for embedding scripts), fallback to steps
    if warmup_ratio is not None and warmup_ratio > 0:
        training_args_kwargs["warmup_ratio"] = warmup_ratio
    elif warmup_steps_val is not None and warmup_steps_val > 0:
        training_args_kwargs["warmup_steps"] = warmup_steps_val

    # save_steps
    if save_steps_val and save_steps_val > 0:
        training_args_kwargs["save_steps"] = save_steps_val
        training_args_kwargs["save_strategy"] = "steps"

    args = SentenceTransformerTrainingArguments(**training_args_kwargs)

    # ── 7. Calculate total steps for progress tracking ──
    if max_steps_val and max_steps_val > 0:
        total_steps = max_steps_val
    else:
        effective_epochs = num_epochs if num_epochs > 0 else 2
        len_dataloader = math.ceil(len(dataset) / batch_size)
        steps_per_epoch = max(len_dataloader // gradient_accumulation_steps, 1)
        total_steps = steps_per_epoch * effective_epochs

    # ── 8. Create progress callback ──
    class _EmbeddingProgressCallback(TrainerCallback):
        """Sends training progress events to the parent process via event_queue."""

        def on_log(self, args, state, control, logs = None, **kwargs):
            if not logs:
                return
            loss_value = logs.get("loss", logs.get("train_loss", None))
            current_step = state.global_step

            elapsed = time.time() - training_start_time
            eta = None
            if current_step > 0 and total_steps > 0:
                remaining = total_steps - current_step
                if remaining > 0:
                    eta = (elapsed / current_step) * remaining

            event_queue.put(
                {
                    "type": "progress",
                    "step": current_step,
                    "epoch": round(state.epoch, 2) if state.epoch else 0,
                    "loss": loss_value,
                    "learning_rate": logs.get("learning_rate", None),
                    "total_steps": total_steps,
                    "elapsed_seconds": elapsed,
                    "eta_seconds": eta,
                    "grad_norm": logs.get("grad_norm"),
                    "num_tokens": getattr(state, "num_input_tokens_seen", None),
                    "eval_loss": logs.get("eval_loss"),
                    "status_message": "",
                    "ts": time.time(),
                }
            )

        def on_step_end(self, args, state, control, **kwargs):
            if _should_stop:
                logger.info("Embedding training: stop at step %d", state.global_step)
                control.should_training_stop = True
                return control

    # ── 9. Create trainer and train ──
    _send_status(event_queue, "Starting embedding training...")
    try:
        trainer = SentenceTransformerTrainer(
            model = model,
            train_dataset = dataset,
            loss = loss,
            args = args,
            callbacks = [_EmbeddingProgressCallback()],
        )

        trainer.train()
    except Exception as e:
        event_queue.put(
            {
                "type": "error",
                "error": f"Embedding training failed: {e}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── 10. Save model ──
    if _should_stop and not _save_on_stop:
        event_queue.put(
            {
                "type": "complete",
                "output_dir": None,
                "status_message": "Training cancelled",
                "ts": time.time(),
            }
        )
        return

    _send_status(event_queue, "Saving model...")
    try:
        model.save_pretrained(output_dir)
        model.tokenizer.save_pretrained(output_dir)
        logger.info("Embedding model saved to %s", output_dir)
    except Exception as e:
        logger.error("Failed to save embedding model: %s", e)
        event_queue.put(
            {
                "type": "error",
                "error": f"Training completed but failed to save: {e}",
                "stack": traceback.format_exc(limit = 20),
                "ts": time.time(),
            }
        )
        return

    # ── 11. Done ──
    event_queue.put(
        {
            "type": "complete",
            "output_dir": output_dir,
            "status_message": "Embedding training completed",
            "ts": time.time(),
        }
    )