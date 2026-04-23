async def start_training(
    request: TrainingStartRequest,
    current_subject: str = Depends(get_current_subject),
):
    """
    Start a training job.

    This endpoint initiates training in the background and returns immediately.
    Use the /status endpoint to check training progress.
    """
    try:
        logger.info(f"Starting training job with model: {request.model_name}")

        # NOTE: No in-process ensure_transformers_version() call here.
        # The subprocess (worker.py) activates the correct version in a
        # fresh Python interpreter before importing any ML libraries.

        backend = get_training_backend()

        # Check if training is already active (before mutating any state)
        if backend.is_training_active():
            existing_job_id: Optional[str] = getattr(backend, "current_job_id", "")
            return TrainingJobResponse(
                job_id = existing_job_id or "",
                status = "error",
                message = (
                    "Training is already in progress. "
                    "Stop current training before starting a new one."
                ),
                error = "Training already active",
            )

        # Generate job ID — passed into start_training() which sets it on the
        # backend only after confirming the old pump thread is dead.
        job_id = (
            f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_uuid.uuid4().hex[:8]}"
        )

        # Validate dataset paths if provided
        if request.local_datasets:
            request.local_datasets = _validate_local_dataset_paths(
                request.local_datasets, "Local dataset"
            )
        if request.local_eval_datasets and request.eval_steps > 0:
            request.local_eval_datasets = _validate_local_dataset_paths(
                request.local_eval_datasets, "Local eval dataset"
            )

        # Convert request to kwargs for backend
        training_kwargs = {
            "model_name": request.model_name,
            "training_type": request.training_type,
            "hf_token": request.hf_token or "",
            "load_in_4bit": request.load_in_4bit,
            "max_seq_length": request.max_seq_length,
            "hf_dataset": request.hf_dataset or "",
            "local_datasets": request.local_datasets,
            "local_eval_datasets": request.local_eval_datasets,
            "format_type": request.format_type,
            "subset": request.subset,
            "train_split": request.train_split,
            "eval_split": request.eval_split,
            "eval_steps": request.eval_steps,
            "dataset_slice_start": request.dataset_slice_start,
            "dataset_slice_end": request.dataset_slice_end,
            "custom_format_mapping": request.custom_format_mapping,
            "num_epochs": request.num_epochs,
            "learning_rate": request.learning_rate,
            "batch_size": request.batch_size,
            "gradient_accumulation_steps": request.gradient_accumulation_steps,
            "warmup_steps": request.warmup_steps,
            "warmup_ratio": request.warmup_ratio,
            "max_steps": request.max_steps,
            "save_steps": request.save_steps,
            "weight_decay": request.weight_decay,
            "random_seed": request.random_seed,
            "packing": request.packing,
            "optim": request.optim,
            "lr_scheduler_type": request.lr_scheduler_type,
            "use_lora": request.use_lora,
            "lora_r": request.lora_r,
            "lora_alpha": request.lora_alpha,
            "lora_dropout": request.lora_dropout,
            "target_modules": request.target_modules
            if request.target_modules
            else None,
            "gradient_checkpointing": request.gradient_checkpointing.strip()
            if request.gradient_checkpointing and request.gradient_checkpointing.strip()
            else "unsloth",
            "use_rslora": request.use_rslora,
            "use_loftq": request.use_loftq,
            "train_on_completions": request.train_on_completions,
            "finetune_vision_layers": request.finetune_vision_layers,
            "finetune_language_layers": request.finetune_language_layers,
            "finetune_attention_modules": request.finetune_attention_modules,
            "finetune_mlp_modules": request.finetune_mlp_modules,
            "is_dataset_image": request.is_dataset_image,
            "is_dataset_audio": request.is_dataset_audio,
            "is_embedding": request.is_embedding,
            "enable_wandb": request.enable_wandb,
            "wandb_token": request.wandb_token or "",
            "wandb_project": request.wandb_project or "",
            "enable_tensorboard": request.enable_tensorboard,
            "tensorboard_dir": request.tensorboard_dir or "",
            "trust_remote_code": request.trust_remote_code,
            "gpu_ids": request.gpu_ids,
        }

        # Training page has no trust_remote_code toggle — the value comes from
        # YAML model defaults applied when the user selects a model.  As a safety
        # net, consult the YAML directly so models that need it always get it.
        if not training_kwargs["trust_remote_code"]:
            model_defaults = load_model_defaults(request.model_name)
            yaml_trust = model_defaults.get("training", {}).get(
                "trust_remote_code", False
            )
            if yaml_trust:
                logger.info(
                    f"YAML config sets trust_remote_code=True for {request.model_name}"
                )
                training_kwargs["trust_remote_code"] = True

        # Free GPU memory: shut down any running inference/export subprocesses
        # before training starts (they'd compete for VRAM otherwise)
        try:
            from core.inference import get_inference_backend

            inf_backend = get_inference_backend()
            if inf_backend.active_model_name:
                logger.info(
                    "Unloading inference model '%s' to free GPU memory for training",
                    inf_backend.active_model_name,
                )
                inf_backend._shutdown_subprocess()
                inf_backend.active_model_name = None
                inf_backend.models.clear()
        except Exception as e:
            logger.warning("Could not unload inference model: %s", e)

        try:
            from core.export import get_export_backend

            exp_backend = get_export_backend()
            if exp_backend.current_checkpoint:
                logger.info(
                    "Shutting down export subprocess to free GPU memory for training"
                )
                exp_backend._shutdown_subprocess()
                exp_backend.current_checkpoint = None
                exp_backend.is_vision = False
                exp_backend.is_peft = False
        except Exception as e:
            logger.warning("Could not shut down export subprocess: %s", e)

        # start_training now spawns a subprocess (non-blocking)
        success = backend.start_training(job_id = job_id, **training_kwargs)

        if not success:
            progress_error = backend.trainer.training_progress.error
            return TrainingJobResponse(
                job_id = backend.current_job_id or "",
                status = "error",
                message = progress_error or "Failed to start training subprocess",
                error = progress_error or "subprocess_start_failed",
            )

        return TrainingJobResponse(
            job_id = job_id,
            status = "queued",
            message = "Training job queued and starting in subprocess",
            error = None,
        )

    except ValueError as e:
        logger.warning("Rejected training GPU selection: %s", e)
        raise HTTPException(status_code = 400, detail = str(e))
    except Exception as e:
        logger.error(f"Error starting training: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500,
            detail = f"Failed to start training: {str(e)}",
        )