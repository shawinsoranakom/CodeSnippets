def load_and_format_dataset(
        self,
        dataset_source: str,
        format_type: str = "auto",
        local_datasets: list = None,
        local_eval_datasets: list = None,
        custom_format_mapping: dict = None,
        subset: str = None,
        train_split: str = "train",
        eval_split: str = None,
        eval_steps: float = 0.00,
        dataset_slice_start: int = None,
        dataset_slice_end: int = None,
    ) -> Optional[tuple]:
        """
        Load and prepare dataset for training.

        Strategy: format first, then split — ensures both train and eval
        portions are properly formatted and templated.

        Returns:
            Tuple of (dataset_info, eval_dataset) or None on error.
            eval_dataset may be None if no eval split is available.
        """
        try:
            dataset = None
            eval_dataset = None
            has_separate_eval_source = (
                False  # True if eval comes from a separate HF split
            )
            eval_enabled = eval_steps is not None and eval_steps > 0

            if local_datasets:
                # Load local datasets using load_dataset() so the result is
                # Arrow-backed (has cache files).  Dataset.from_list() creates
                # an in-memory dataset with no cache, which forces num_proc=1
                # during tokenization/map because sharding requires Arrow files.
                all_files = self._resolve_local_files(local_datasets)

                if all_files:
                    loader = self._loader_for_files(all_files)
                    dataset = load_dataset(loader, data_files = all_files, split = "train")

                    # Check if stopped during dataset loading
                    if self.should_stop:
                        logger.info("Stopped during dataset loading\n")
                        return None

                    self._update_progress(
                        status_message = f"Loaded {len(dataset)} samples from local files"
                    )
                    logger.info(f"Loaded {len(dataset)} samples from local files\n")
                    logger.info(f"[DEBUG] Dataset cache_files: {dataset.cache_files}\n")

                # Load local eval datasets if provided
                if local_eval_datasets and eval_enabled:
                    eval_all_files = self._resolve_local_files(local_eval_datasets)
                    if eval_all_files:
                        eval_loader = self._loader_for_files(eval_all_files)
                        eval_dataset = load_dataset(
                            eval_loader, data_files = eval_all_files, split = "train"
                        )
                        has_separate_eval_source = True
                        logger.info(
                            f"Loaded {len(eval_dataset)} eval samples from local eval files\n"
                        )

            elif dataset_source:
                # Load from Hugging Face
                split_name = train_split or "train"
                load_kwargs = {"path": dataset_source, "split": split_name}
                if subset:
                    load_kwargs["name"] = subset

                _slice_start = dataset_slice_start or 0
                if (
                    dataset_slice_end is not None
                    and dataset_slice_end >= 0
                    and dataset_slice_end >= _slice_start
                ):
                    # Manual slice — stream only the rows we need instead of
                    # downloading the entire dataset.
                    rows_to_stream = dataset_slice_end + 1
                    logger.info(
                        f"[dataset-slice] Manual slice specified "
                        f"(start={dataset_slice_start}, end={dataset_slice_end}), "
                        f"streaming {rows_to_stream} rows\n"
                    )
                    stream = load_dataset(**load_kwargs, streaming = True)
                    dataset = Dataset.from_list(list(stream.take(rows_to_stream)))
                    logger.info(
                        f"[dataset-slice] Downloaded {len(dataset)} rows "
                        f"(requested {rows_to_stream})\n"
                    )
                    self._update_progress(
                        status_message = f"Streamed {len(dataset)} rows from HuggingFace"
                    )
                else:
                    self._update_progress(
                        status_message = f"Downloading dataset: {dataset_source}..."
                    )
                    dataset = load_dataset(**load_kwargs)

                # Check if stopped during dataset loading
                if self.should_stop:
                    logger.info("Stopped during dataset loading\n")
                    return None

                n_rows = len(dataset) if hasattr(dataset, "__len__") else 0
                self._update_progress(
                    status_message = f"Downloaded {dataset_source} ({n_rows:,} rows)"
                )
                logger.info(
                    f"Loaded dataset from Hugging Face: {dataset_source} ({n_rows:,} rows)\n"
                )

                # Resolve eval split from a separate HF split (explicit or auto-detected)
                if eval_enabled:
                    effective_train = train_split or "train"
                    if eval_split and eval_split != effective_train:
                        # Explicit eval split provided - load it directly
                        logger.info(f"Loading explicit eval split: '{eval_split}'\n")
                        eval_load_kwargs = {"path": dataset_source, "split": eval_split}
                        if subset:
                            eval_load_kwargs["name"] = subset
                        eval_dataset = load_dataset(**eval_load_kwargs)
                        has_separate_eval_source = True
                        logger.info(
                            f"Loaded eval split '{eval_split}' with {len(eval_dataset)} rows\n"
                        )
                    elif eval_split and eval_split == effective_train:
                        # Same split as training — will do 80/20 split after formatting
                        logger.info(
                            f"Eval split '{eval_split}' is the same as train split — will split 80/20\n"
                        )
                    else:
                        # Auto-detect eval split from HF (returns a separate dataset, or None)
                        eval_dataset = self._auto_detect_eval_split_from_hf(
                            dataset_source = dataset_source,
                            subset = subset,
                        )
                        if eval_dataset is not None:
                            has_separate_eval_source = True
                else:
                    logger.info(
                        "Eval disabled (eval_steps <= 0), skipping eval split detection\n"
                    )

            if dataset is None:
                raise ValueError("No dataset provided")

            # Apply index range slicing if requested (inclusive on both ends)
            if dataset_slice_start is not None or dataset_slice_end is not None:
                total_rows = len(dataset)
                start = dataset_slice_start if dataset_slice_start is not None else 0
                end = (
                    dataset_slice_end
                    if dataset_slice_end is not None
                    else total_rows - 1
                )
                # Clamp to valid range
                start = max(0, min(start, total_rows - 1))
                end = max(start, min(end, total_rows - 1))
                dataset = dataset.select(range(start, end + 1))
                logger.info(
                    f"Sliced dataset to rows [{start}, {end}]: {len(dataset)} of {total_rows} rows\n"
                )
                self._update_progress(
                    status_message = f"Sliced dataset to {len(dataset)} rows (indices {start}-{end})"
                )

            # Check if stopped before applying template
            if self.should_stop:
                logger.info("Stopped before applying chat template\n")
                return None

            # ========== AUDIO MODELS: custom preprocessing ==========
            if self._audio_type == "csm":
                processed = self._preprocess_csm_dataset(dataset, custom_format_mapping)
                return (processed, None)

            elif self._audio_type == "whisper":
                train_data, eval_data = self._preprocess_whisper_dataset(
                    dataset,
                    eval_split = eval_split,
                    custom_format_mapping = custom_format_mapping,
                )
                return (train_data, eval_data)

            elif self._audio_type == "snac":
                processed = self._preprocess_snac_dataset(
                    dataset, custom_format_mapping
                )
                return (processed, None)

            elif self._audio_type == "bicodec":
                processed = self._preprocess_bicodec_dataset(
                    dataset, custom_format_mapping
                )
                return ({"dataset": processed, "final_format": "audio_bicodec"}, None)

            elif self._audio_type == "dac":
                processed = self._preprocess_dac_dataset(dataset, custom_format_mapping)
                return ({"dataset": processed, "final_format": "audio_dac"}, None)

            elif self.is_audio_vlm:
                formatted = self._format_audio_vlm_dataset(
                    dataset, custom_format_mapping
                )
                return (formatted, None)

            # ========== FORMAT FIRST ==========
            logger.info(f"Formatting dataset with format_type='{format_type}'...\n")

            dataset_info = format_and_template_dataset(
                dataset,
                model_name = self.model_name,
                tokenizer = self.tokenizer,
                is_vlm = self.is_vlm,
                format_type = format_type,
                dataset_name = dataset_source,
                custom_format_mapping = custom_format_mapping,
                progress_callback = self._update_progress,
            )

            # Check if stopped during formatting
            if self.should_stop:
                logger.info("Stopped during dataset formatting\n")
                return None

            # Abort if dataset formatting/conversion failed
            if not dataset_info.get("success", True):
                errors = dataset_info.get("errors", [])
                error_msg = "; ".join(errors) if errors else "Dataset formatting failed"
                logger.error(f"Dataset conversion failed: {error_msg}")
                self._update_progress(error = error_msg)
                return None

            detected = dataset_info.get("detected_format", "unknown")
            final_ds = dataset_info.get("dataset")
            final_n = len(final_ds) if hasattr(final_ds, "__len__") else "?"
            self._update_progress(
                status_message = f"Dataset ready ({final_n:,} samples, {detected} format)"
            )
            logger.info(
                f"Dataset formatted successfully ({final_n} samples, {detected})\n"
            )

            # ========== THEN SPLIT ==========
            if has_separate_eval_source and eval_dataset is not None:
                # Eval came from a separate HF split — format it too
                logger.info(f"Formatting eval dataset ({len(eval_dataset)} rows)...\n")
                eval_info = format_and_template_dataset(
                    eval_dataset,
                    model_name = self.model_name,
                    tokenizer = self.tokenizer,
                    is_vlm = self.is_vlm,
                    format_type = format_type,
                    dataset_name = dataset_source,
                    custom_format_mapping = custom_format_mapping,
                )
                eval_dataset = eval_info["dataset"]
                logger.info(f"Eval dataset formatted successfully\n")
            elif eval_enabled and not has_separate_eval_source:
                # No separate eval source — split the already-formatted dataset
                formatted_dataset = dataset_info["dataset"]
                split_result = self._resolve_eval_split_from_dataset(formatted_dataset)
                if split_result is not None:
                    train_portion, eval_dataset = split_result
                    dataset_info["dataset"] = train_portion

            return (dataset_info, eval_dataset)

        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            self._update_progress(error = str(e))
            return None