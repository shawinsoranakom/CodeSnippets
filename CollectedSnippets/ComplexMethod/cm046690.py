def _train_worker(self, dataset: Dataset, **training_args):
        """Worker function for training (runs in separate thread)"""
        try:
            # On spawn-based platforms (Windows, macOS), register all known
            # compiled-cache directories on sys.path and PYTHONPATH before any
            # dataset.map() call so spawned workers can import dynamically
            # compiled modules such as UnslothSFTTrainer.
            if sys.platform in ("win32", "darwin"):
                from utils.cache_cleanup import register_compiled_cache_on_path

                register_compiled_cache_on_path()

            # Store training parameters for metrics calculation
            self.batch_size = training_args.get("batch_size", 2)
            self.max_seq_length = training_args.get("max_seq_length", 2048)
            self.gradient_accumulation_steps = training_args.get(
                "gradient_accumulation_steps", 4
            )

            # Set training start time
            self.training_start_time = time.time()

            self._update_progress(is_training = True, error = None)

            # Setup logging
            if training_args.get("enable_wandb", False) and training_args.get(
                "wandb_token"
            ):
                os.environ["WANDB_API_KEY"] = training_args["wandb_token"]
                import wandb

                wandb.init(
                    project = training_args.get("wandb_project", "unsloth-training")
                )

            # Create output directory
            output_dir = str(resolve_output_dir(training_args.get("output_dir")))
            ensure_dir(Path(output_dir))

            # ========== AUDIO TRAINER BRANCH ==========
            if self._audio_type == "csm":
                # CSM uses plain HF Trainer (NOT SFTTrainer)
                # Needs remove_unused_columns=False for depth decoder (input_values + cutoffs)
                from transformers import Trainer as HFTrainer, TrainingArguments

                self._apply_csm_forward_fix()

                config = self._build_audio_training_args(
                    training_args,
                    output_dir,
                    extra_args = {
                        "remove_unused_columns": False,
                    },
                )
                self.trainer = HFTrainer(
                    model = self.model,
                    train_dataset = dataset,
                    args = TrainingArguments(**config),
                )
                self.trainer.add_callback(self._create_progress_callback())

                batch_size = training_args.get("batch_size", 2)
                total = self._calculate_total_steps(
                    len(dataset),
                    batch_size,
                    training_args.get("gradient_accumulation_steps", 4),
                    training_args.get("num_epochs", 3),
                    training_args.get("max_steps", 0),
                )
                self._update_progress(
                    total_steps = total, status_message = "Starting CSM training..."
                )
                logger.info(f"CSM training config: {config}\n")
                self.trainer.train()
                self._finalize_training(output_dir, "CSM")
                return

            elif self._audio_type == "snac":
                # Orpheus: language model with SNAC codec tokens — plain HF Trainer
                # DataCollatorForSeq2Seq dynamically pads variable-length sequences per batch
                # (text + audio codes vary in length) and pads labels with -100.
                from transformers import (
                    Trainer as HFTrainer,
                    TrainingArguments,
                    DataCollatorForSeq2Seq,
                )

                config = self._build_audio_training_args(training_args, output_dir)
                self.trainer = HFTrainer(
                    model = self.model,
                    train_dataset = dataset,
                    args = TrainingArguments(**config),
                    data_collator = DataCollatorForSeq2Seq(
                        tokenizer = self.tokenizer,
                        padding = True,
                        pad_to_multiple_of = 8,
                    ),
                )
                self.trainer.add_callback(self._create_progress_callback())

                batch_size = training_args.get("batch_size", 2)
                total = self._calculate_total_steps(
                    len(dataset),
                    batch_size,
                    training_args.get("gradient_accumulation_steps", 4),
                    training_args.get("num_epochs", 3),
                    training_args.get("max_steps", 0),
                )
                self._update_progress(
                    total_steps = total, status_message = "Starting SNAC training..."
                )
                logger.info(f"SNAC training config: {config}\n")
                self.trainer.train()
                self._finalize_training(output_dir, "SNAC")
                return

            elif self._audio_type == "whisper":
                # Whisper: Seq2SeqTrainer with custom speech collator
                from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments
                from utils.datasets import DataCollatorSpeechSeq2SeqWithPadding

                eval_dataset = training_args.get("eval_dataset", None)
                extra = {"remove_unused_columns": False, "label_names": ["labels"]}
                if eval_dataset:
                    extra["eval_strategy"] = "steps"
                    extra["eval_steps"] = training_args.get("eval_steps", 5)

                config = self._build_audio_training_args(
                    training_args, output_dir, extra_args = extra
                )

                trainer_kwargs = {
                    "model": self.model,
                    "train_dataset": dataset,
                    "data_collator": DataCollatorSpeechSeq2SeqWithPadding(
                        processor = self.tokenizer
                    ),
                    "processing_class": self.tokenizer.feature_extractor,
                    "args": Seq2SeqTrainingArguments(**config),
                }
                if eval_dataset:
                    trainer_kwargs["eval_dataset"] = eval_dataset

                self.trainer = Seq2SeqTrainer(**trainer_kwargs)
                self.trainer.add_callback(self._create_progress_callback())

                batch_size = training_args.get("batch_size", 2)
                total = self._calculate_total_steps(
                    len(dataset),
                    batch_size,
                    training_args.get("gradient_accumulation_steps", 4),
                    training_args.get("num_epochs", 3),
                    training_args.get("max_steps", 0),
                )
                self._update_progress(
                    total_steps = total, status_message = "Starting Whisper training..."
                )
                logger.info(f"Whisper training config: {config}\n")
                self.trainer.train()
                self._finalize_training(output_dir, "Whisper")
                return

            elif self._audio_type is not None and self._audio_type not in (
                "bicodec",
                "dac",
            ):
                # bicodec/dac use the standard SFTTrainer text path below
                raise NotImplementedError(
                    f"Audio training for '{self._audio_type}' not yet implemented"
                )

            # ========== DATA COLLATOR SELECTION ==========
            # Detect special model types
            model_name_lower = self.model_name.lower()
            is_deepseek_ocr = (
                "deepseek" in model_name_lower and "ocr" in model_name_lower
            )

            logger.info("Configuring data collator...\n")

            data_collator = None  # Default to built-in data collator
            if is_deepseek_ocr:
                # Special DeepSeek OCR collator - auto-install if needed
                logger.info("Detected DeepSeek OCR model\n")
                # Ensure DeepSeek OCR module is installed
                if not _ensure_deepseek_ocr_installed():
                    error_msg = (
                        "Failed to install DeepSeek OCR module. "
                        "Please install manually: "
                        "from huggingface_hub import snapshot_download; "
                        "snapshot_download('unsloth/DeepSeek-OCR', local_dir='deepseek_ocr')"
                    )
                    logger.error(error_msg)
                    self._update_progress(error = error_msg, is_training = False)
                    return

                try:
                    from backend.data_utils import DeepSeekOCRDataCollator

                    logger.info("Configuring DeepSeek OCR data collator...\n")
                    FastVisionModel.for_training(self.model)
                    data_collator = DeepSeekOCRDataCollator(
                        tokenizer = self.tokenizer,
                        model = self.model,
                        image_size = 640,
                        base_size = 1024,
                        crop_mode = True,
                        train_on_responses_only = training_args.get(
                            "train_on_completions", False
                        ),
                    )
                    logger.info("DeepSeek OCR data collator configured successfully\n")

                except Exception as e:
                    logger.error(f"Failed to configure DeepSeek OCR collator: {e}")
                    error_msg = f"Error configuring DeepSeek OCR: {str(e)}"
                    self._update_progress(error = error_msg, is_training = False)
                    return

            elif self.is_audio_vlm:
                # Audio VLM collator (e.g. Gemma 3N with audio data)
                # Mirrors the collate_fn from Gemma3N_(4B)-Audio notebook
                logger.info("Configuring audio VLM data collator...\n")
                processor = self.tokenizer  # FastModel returns processor as tokenizer

                audio_col_name = getattr(self, "_audio_vlm_audio_col", "audio")

                def audio_vlm_collate_fn(examples):
                    texts = []
                    audios = []
                    for example in examples:
                        text = processor.apply_chat_template(
                            example["messages"],
                            tokenize = False,
                            add_generation_prompt = False,
                        ).strip()
                        texts.append(text)
                        audios.append(example[audio_col_name]["array"])

                    batch = processor(
                        text = texts, audio = audios, return_tensors = "pt", padding = True
                    )

                    # Labels = input_ids with special tokens masked
                    labels = batch["input_ids"].clone()
                    labels[labels == processor.tokenizer.pad_token_id] = -100
                    for attr in (
                        "audio_token_id",
                        "image_token_id",
                        "boi_token_id",
                        "eoi_token_id",
                    ):
                        token_id = getattr(processor.tokenizer, attr, None)
                        if token_id is not None:
                            labels[labels == token_id] = -100
                    batch["labels"] = labels
                    return batch

                data_collator = audio_vlm_collate_fn
                logger.info("Audio VLM data collator configured\n")

            elif self.is_vlm:
                # Standard VLM collator (images)
                logger.info("Using UnslothVisionDataCollator for vision model\n")
                from unsloth.trainer import UnslothVisionDataCollator

                FastVisionModel.for_training(self.model)
                data_collator = UnslothVisionDataCollator(self.model, self.tokenizer)
                logger.info("Vision data collator configured\n")

            # ========== TRAINING CONFIGURATION ==========
            # Handle warmup_steps vs warmup_ratio
            warmup_steps_val = training_args.get("warmup_steps", None)
            warmup_ratio_val = training_args.get("warmup_ratio", None)

            lr_value = training_args.get("learning_rate", 2e-4)
            logger.info(
                f"[DEBUG] learning_rate from training_args: {lr_value} (type: {type(lr_value).__name__})\n"
            )

            config_args = {
                "per_device_train_batch_size": training_args.get("batch_size", 2),
                "gradient_accumulation_steps": training_args.get(
                    "gradient_accumulation_steps", 4
                ),
                "num_train_epochs": training_args.get(
                    "num_epochs", 3
                ),  # Default to epochs
                "learning_rate": lr_value,
                "fp16": not is_bfloat16_supported(),
                "bf16": is_bfloat16_supported(),
                "logging_steps": 1,
                "weight_decay": training_args.get("weight_decay", 0.001),
                "seed": training_args.get("random_seed", 3407),
                "output_dir": output_dir,
                "report_to": _build_report_targets(training_args),
                "include_num_input_tokens_seen": True,  # Enable token counting
                "dataset_num_proc": dataset_map_num_proc(
                    1
                    if (self.is_audio or self.is_audio_vlm or self._cuda_audio_used)
                    else max(1, (os.cpu_count() or 1) // 4)
                ),
                "max_seq_length": training_args.get("max_seq_length", 2048),
            }
            if training_args.get("enable_tensorboard", False):
                config_args["logging_dir"] = str(
                    resolve_tensorboard_dir(training_args.get("tensorboard_dir"))
                )
            logger.info(
                f"[DEBUG] dataset_num_proc={config_args['dataset_num_proc']} (is_audio={self.is_audio}, is_audio_vlm={self.is_audio_vlm}, _cuda_audio_used={self._cuda_audio_used})"
            )

            # On spawn-based platforms (Windows, macOS) with transformers 5.x,
            # disable DataLoader multiprocessing to avoid issues with modified
            # sys.path (.venv_t5) in spawned workers.
            if sys.platform in ("win32", "darwin"):
                import transformers as _tf

                if _tf.__version__.startswith("5."):
                    config_args["dataloader_num_workers"] = 0

            # Add warmup parameter - use warmup_ratio if provided, otherwise warmup_steps
            if warmup_ratio_val is not None:
                config_args["warmup_ratio"] = warmup_ratio_val
                logger.info(f"Using warmup_ratio: {warmup_ratio_val}\n")
            elif warmup_steps_val is not None:
                config_args["warmup_steps"] = warmup_steps_val
                logger.info(f"Using warmup_steps: {warmup_steps_val}\n")
            else:
                # Default to warmup_steps if neither provided
                config_args["warmup_steps"] = 5
                logger.info(f"Using default warmup_steps: 5\n")

            # Add save_steps if specified
            save_steps_val = training_args.get("save_steps", 0)
            if save_steps_val and save_steps_val > 0:
                config_args["save_steps"] = save_steps_val
                config_args["save_strategy"] = "steps"

            #  If max_steps is specified, use it instead of epochs
            max_steps_val = training_args.get("max_steps", 0)
            if max_steps_val and max_steps_val > 0:
                del config_args["num_train_epochs"]  # Remove epochs
                config_args["max_steps"] = max_steps_val  # Use steps instead
                logger.info(f"Training for {max_steps_val} steps\n")
            else:
                logger.info(f"Training for {config_args['num_train_epochs']} epochs\n")

            # ========== EVAL CONFIGURATION ==========
            eval_dataset = training_args.get("eval_dataset", None)
            eval_steps_val = training_args.get("eval_steps", 0.00)
            if eval_dataset is not None:
                if eval_steps_val > 0:
                    config_args["eval_strategy"] = "steps"
                    config_args["eval_steps"] = eval_steps_val
                    logger.info(
                        f"✅ Evaluation enabled: eval_steps={eval_steps_val} (fraction of total steps)\n"
                    )
                    logger.info(f"Eval dataset: {len(eval_dataset)} rows\n")
                else:
                    logger.info(
                        f"⚠️  Eval dataset provided but eval_steps={eval_steps_val} (disabled)\n"
                    )
                    logger.info("To enable evaluation, set eval_steps > 0.0\n")
            else:
                logger.info("No eval dataset — evaluation disabled\n")

            # Add model-specific parameters
            # Use optim and lr_scheduler_type from training_args if provided, otherwise use defaults
            optim_value = training_args.get("optim", "adamw_8bit")
            lr_scheduler_type_value = training_args.get("lr_scheduler_type", "linear")

            if self.is_vlm or self.is_audio_vlm:
                # Vision / audio VLM config (both need skip_prepare_dataset + remove_unused_columns)
                label = "audio VLM" if self.is_audio_vlm else "vision"
                logger.info(f"Configuring {label} model training parameters\n")
                # Use provided values or defaults for vision models
                optim_value = training_args.get("optim", "adamw_torch_fused")
                lr_scheduler_type_value = training_args.get(
                    "lr_scheduler_type", "cosine"
                )
                config_args.update(
                    {
                        "optim": optim_value,
                        "lr_scheduler_type": lr_scheduler_type_value,
                        "gradient_checkpointing": True,
                        "gradient_checkpointing_kwargs": {"use_reentrant": False},
                        "max_grad_norm": 0.3,
                        "remove_unused_columns": False,
                        "dataset_text_field": "",
                        "dataset_kwargs": {"skip_prepare_dataset": True},
                        "max_length": training_args.get("max_seq_length", 2048),
                    }
                )
            else:
                logger.info("Configuring text model training parameters\n")
                config_args.update(
                    {
                        "optim": optim_value,
                        "lr_scheduler_type": lr_scheduler_type_value,
                        "dataset_text_field": "text",
                    }
                )

                # Only add packing for text models (not DeepSeek OCR which is VLM)
                if not is_deepseek_ocr:
                    packing_enabled = training_args.get("packing", False)
                    config_args["packing"] = packing_enabled
                    logger.info(
                        f"Sequence packing: {'enabled' if packing_enabled else 'disabled'}\n"
                    )

            # Audio codec overrides — BiCodec/DAC use the text SFTTrainer path
            if self._audio_type == "bicodec":
                config_args["packing"] = False
                logger.info("Applied BiCodec overrides: packing=False\n")
            elif self._audio_type == "dac":
                config_args["packing"] = False
                logger.info("Applied DAC overrides: packing=False\n")

            logger.info(f"The configuration is: {config_args}")

            logger.info("Training configuration prepared\n")
            # ========== TRAINER INITIALIZATION ==========
            if self.is_audio_vlm:
                # Audio VLM (e.g. Gemma 3N + audio): raw Dataset from _format_audio_vlm_dataset
                # Notebook uses processing_class=processor.tokenizer (text tokenizer only)
                train_dataset = (
                    dataset if isinstance(dataset, Dataset) else dataset["dataset"]
                )
                processing_class = (
                    self.tokenizer.tokenizer
                    if hasattr(self.tokenizer, "tokenizer")
                    else self.tokenizer
                )
                trainer_kwargs = {
                    "model": self.model,
                    "train_dataset": train_dataset,
                    "processing_class": processing_class,
                    "data_collator": data_collator,
                    "args": SFTConfig(**config_args),
                }
                if eval_dataset is not None:
                    trainer_kwargs["eval_dataset"] = eval_dataset
                self.trainer = SFTTrainer(**trainer_kwargs)
            elif self.is_vlm:
                # Image VLM: dataset is dict wrapper from format_and_template_dataset
                train_dataset = (
                    dataset["dataset"] if isinstance(dataset, dict) else dataset
                )
                trainer_kwargs = {
                    "model": self.model,
                    "train_dataset": train_dataset,
                    "processing_class": self.tokenizer,
                    "data_collator": data_collator,
                    "args": SFTConfig(**config_args),
                }
                if eval_dataset is not None:
                    trainer_kwargs["eval_dataset"] = eval_dataset
                self.trainer = SFTTrainer(**trainer_kwargs)
            else:
                # For text-only training, if the tokenizer is actually a Processor
                # (e.g., Gemma-3 returns a ProcessorMixin even for text), we must
                # unwrap to the raw tokenizer. Otherwise Unsloth's SFTTrainer detects
                # ProcessorMixin → sets _is_vlm=True → skips _prepare_dataset entirely,
                # and the 'text' column never gets tokenized to 'input_ids'.
                from transformers import ProcessorMixin

                sft_tokenizer = self.tokenizer
                if isinstance(self.tokenizer, ProcessorMixin) and hasattr(
                    self.tokenizer, "tokenizer"
                ):
                    logger.info(
                        f"  ⚠️ Unwrapping Processor → raw tokenizer for text-only SFTTrainer"
                    )
                    sft_tokenizer = self.tokenizer.tokenizer

                trainer_kwargs = {
                    "model": self.model,
                    "tokenizer": sft_tokenizer,
                    "train_dataset": dataset["dataset"],
                    "data_collator": data_collator,
                    "args": SFTConfig(**config_args),
                }
                if eval_dataset is not None:
                    trainer_kwargs["eval_dataset"] = eval_dataset
                self.trainer = SFTTrainer(**trainer_kwargs)
                # Restore the full processor as processing_class so checkpoint
                # saves include preprocessor_config.json (needed for GGUF export).
                if sft_tokenizer is not self.tokenizer:
                    self.trainer.processing_class = self.tokenizer
            logger.info("Trainer initialized\n")

            # ========== TRAIN ON RESPONSES ONLY ==========
            # Determine if we should train on responses only
            instruction_part = None
            response_part = None
            train_on_responses_enabled = training_args.get(
                "train_on_completions", False
            )

            # DeepSeek OCR handles this internally in its collator, so skip
            # Audio VLM handles label masking in its collator, so skip
            if (
                train_on_responses_enabled
                and not self.is_audio_vlm
                and not self.is_audio
                and not (is_deepseek_ocr or dataset["final_format"].lower() == "alpaca")
            ):
                try:
                    logger.info("Configuring train on responses only...\n")

                    # Get the template mapping for this model
                    model_name_lower = self.model_name.lower()

                    if model_name_lower in MODEL_TO_TEMPLATE_MAPPER:
                        template_name = MODEL_TO_TEMPLATE_MAPPER[model_name_lower]
                        logger.info(f"Detected template: {template_name}\n")

                        if template_name in TEMPLATE_TO_RESPONSES_MAPPER:
                            instruction_part = TEMPLATE_TO_RESPONSES_MAPPER[
                                template_name
                            ]["instruction"]
                            response_part = TEMPLATE_TO_RESPONSES_MAPPER[template_name][
                                "response"
                            ]

                            logger.info(
                                f"Instruction marker: {instruction_part[:50]}...\n"
                            )
                            logger.info(f"Response marker: {response_part[:50]}...\n")
                        else:
                            logger.info(
                                f"No response mapping found for template: {template_name}\n"
                            )
                            train_on_responses_enabled = False
                    else:
                        logger.info(
                            f"No template mapping found for model: {self.model_name}\n"
                        )
                        train_on_responses_enabled = False

                except Exception as e:
                    logger.warning(f"Could not configure train on responses: {e}")
                    train_on_responses_enabled = False

            # Apply train on responses only if we have valid parts
            if (
                train_on_responses_enabled
                and instruction_part
                and response_part
                and not self.is_audio_vlm
                and not self.is_audio
                and not (is_deepseek_ocr or dataset["final_format"].lower() == "alpaca")
            ):
                try:
                    from unsloth.chat_templates import train_on_responses_only

                    self.trainer = train_on_responses_only(
                        self.trainer,
                        instruction_part = instruction_part,
                        response_part = response_part,
                        num_proc = config_args["dataset_num_proc"],
                    )
                    logger.info("Train on responses only configured successfully\n")

                    # ── Safety net: check if all samples were filtered out ──
                    # Unsloth's train_on_responses_only masks non-response
                    # tokens with -100. If max_seq_length is too short and the
                    # response portion gets truncated away, EVERY sample ends
                    # up with all labels == -100 and Unsloth removes them,
                    # leaving 0 usable training samples.
                    filtered_len = len(self.trainer.train_dataset)
                    original_len = len(dataset["dataset"])
                    dropped = original_len - filtered_len
                    drop_pct = (
                        round(100 * dropped / original_len, 1)
                        if original_len > 0
                        else 0
                    )

                    if filtered_len == 0 or drop_pct > 30:
                        max_seq = training_args.get("max_seq_length", 2048)
                        error_msg = (
                            f"{dropped}/{original_len} samples ({drop_pct}%) "
                            f"were dropped after applying 'train on responses "
                            f"only' — only {filtered_len} remain. This usually "
                            f"means max_seq_length ({max_seq}) is too short "
                            f"and the response portion is being truncated "
                            f"away. Try increasing max_seq_length (e.g. 8192) "
                            f"or disabling 'Train on completions'."
                        )
                        logger.error(error_msg)
                        self._update_progress(error = error_msg, is_training = False)
                        return

                    if dropped > 0:
                        logger.info(
                            f"⚠️ {dropped}/{original_len} samples "
                            f"({drop_pct}%) were dropped (all labels "
                            f"masked). {filtered_len} samples remain.\n"
                        )
                    logger.info(f"Post-filter dataset size: {filtered_len} samples\n")

                    # [DEBUG] Decode first sample AFTER train_on_completions applied
                    # try:
                    #     _row = self.trainer.train_dataset[0]
                    #     _space = self.tokenizer(
                    #         " ", add_special_tokens = False
                    #     ).input_ids[0]
                    #     print("[DEBUG] === After train_on_completions ===", flush = True)
                    #     print(
                    #         f"[DEBUG] input_ids decoded:\n{self.tokenizer.decode(_row['input_ids'])}\n",
                    #         flush = True,
                    #     )
                    #     print(
                    #         f"[DEBUG] labels decoded (-100 → space):\n{self.tokenizer.decode([_space if x == -100 else x for x in _row['labels']])}\n",
                    #         flush = True,
                    #     )
                    # except Exception as _dbg_e:
                    #     print(
                    #         f"[DEBUG] Could not decode post-completions sample: {_dbg_e}",
                    #         flush = True,
                    #     )

                except Exception as e:
                    logger.warning(f"Failed to apply train on responses only: {e}")
                    train_on_responses_enabled = False
            else:
                if train_on_responses_enabled and is_deepseek_ocr:
                    logger.info("Train on responses handled by DeepSeek OCR collator\n")
                else:
                    logger.info("Training on full sequences (including prompts)\n")

            # ========== PROGRESS TRACKING ==========
            self.trainer.add_callback(self._create_progress_callback())

            num_samples = len(
                dataset["dataset"] if isinstance(dataset, dict) else dataset
            )
            batch_size = training_args.get("batch_size", 2)
            total_steps = self._calculate_total_steps(
                num_samples,
                batch_size,
                training_args.get("gradient_accumulation_steps", 4),
                training_args.get("num_epochs", 3),
                training_args.get("max_steps", 0),
            )
            self._update_progress(total_steps = total_steps)

            # ========== START TRAINING ==========
            self._update_progress(status_message = "Starting training...")
            logger.info("Starting training...\n")
            self.trainer.train()

            # ========== SAVE MODEL ==========
            self._finalize_training(output_dir)

        except Exception as e:
            import traceback

            logger.error(f"Training error: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            self._update_progress(is_training = False, error = str(e))

        finally:
            self.is_training = False