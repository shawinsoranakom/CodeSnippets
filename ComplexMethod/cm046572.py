def check_format(
    request: CheckFormatRequest,
    current_subject: str = Depends(get_current_subject),
):
    """
    Check if a dataset requires manual column mapping.

    Strategy for HuggingFace datasets:
      1. list_repo_files → pick the first data file → load_dataset(data_files=[…])
         Avoids resolving thousands of files; typically ~2-4 s.
      2. Full streaming load_dataset as a last-resort fallback.

    Local files are loaded directly.

    Using a plain `def` (not async) so FastAPI runs this in a thread-pool,
    preventing any blocking IO from freezing the event loop.
    """
    try:
        from itertools import islice
        from datasets import Dataset, load_dataset
        from utils.datasets import format_dataset

        PREVIEW_SIZE = 10

        logger.info(f"Checking format for dataset: {request.dataset_name}")

        dataset_path = resolve_dataset_path(request.dataset_name)
        total_rows = None

        if dataset_path.exists():
            # ── Local file ──────────────────────────────────────────
            train_split = request.train_split or "train"
            preview_slice, total_rows = _load_local_preview_slice(
                dataset_path = dataset_path,
                train_split = train_split,
                preview_size = PREVIEW_SIZE,
            )
        else:
            # ── HuggingFace dataset ─────────────────────────────────
            # Tier 1: list_repo_files → load only the first data file
            preview_slice = None

            try:
                from huggingface_hub import HfApi

                api = HfApi()
                repo_files = api.list_repo_files(
                    request.dataset_name,
                    repo_type = "dataset",
                    token = request.hf_token or None,
                )
                data_files = [
                    f for f in repo_files if any(f.endswith(ext) for ext in DATA_EXTS)
                ]

                # Prefer tabular formats over archives (e.g. images.zip → ImageFolder
                # with synthetic image/label columns that don't match the real schema).
                tabular_files = [
                    f
                    for f in data_files
                    if any(f.endswith(ext) for ext in _TABULAR_EXTS)
                ]
                candidates = tabular_files or data_files

                # When a subset is specified, narrow to files whose name matches
                # (e.g. subset="testmini" → prefer "testmini.parquet").
                if request.subset and candidates:
                    subset_matches = [
                        f for f in candidates if request.subset in Path(f).stem
                    ]
                    if subset_matches:
                        candidates = subset_matches

                if candidates:
                    first_file = candidates[0]
                    logger.info(f"Tier 1: loading single file {first_file}")
                    load_kwargs = {
                        "path": request.dataset_name,
                        "data_files": [first_file],
                        "split": "train",
                        "streaming": True,
                    }
                    if request.hf_token:
                        load_kwargs["token"] = request.hf_token

                    streamed_ds = load_dataset(**load_kwargs)
                    rows = list(islice(streamed_ds, PREVIEW_SIZE))
                    if rows:
                        preview_slice = Dataset.from_list(rows)
            except Exception as e:
                logger.warning(f"Tier 1 (single-file) failed: {e}")

            if preview_slice is None:
                # Tier 2: full streaming (resolves all files — slow for large repos)
                logger.info("Tier 2: falling back to full streaming load_dataset")
                load_kwargs = {
                    "path": request.dataset_name,
                    "split": request.train_split,
                    "streaming": True,
                }
                if request.subset:
                    load_kwargs["name"] = request.subset
                if request.hf_token:
                    load_kwargs["token"] = request.hf_token

                streamed_ds = load_dataset(**load_kwargs)

                rows = list(islice(streamed_ds, PREVIEW_SIZE))
                if not rows:
                    raise HTTPException(
                        status_code = 400,
                        detail = "Dataset appears to be empty or could not be streamed",
                    )

                preview_slice = Dataset.from_list(rows)
            total_rows = None

        # Run lightweight format check on the preview slice
        result = check_dataset_format(preview_slice, is_vlm = request.is_vlm)

        logger.info(
            f"Format check result: requires_mapping={result['requires_manual_mapping']}, format={result['detected_format']}, is_image={result.get('is_image', False)}"
        )

        # Generate preview samples
        preview_samples = None
        if not result["requires_manual_mapping"]:
            if result.get("suggested_mapping"):
                # Heuristic-detected: show raw data so columns match the API response.
                # Processing (column stripping) happens at training time, not preview.
                preview_samples = _serialize_preview_rows(preview_slice)
            else:
                try:
                    format_result = format_dataset(
                        preview_slice,
                        format_type = "auto",
                        num_proc = None,  # Only 10 preview rows -- no need for multiprocessing
                    )
                    processed = format_result["dataset"]
                    preview_samples = _serialize_preview_rows(processed)
                except Exception as e:
                    logger.warning(
                        f"Processed preview generation failed (non-fatal): {e}"
                    )
                    preview_samples = _serialize_preview_rows(preview_slice)
        else:
            preview_samples = _serialize_preview_rows(preview_slice)

        # Collect warnings: from check_dataset_format + URL-based image detection
        warning = result.get("warning")
        image_col = result.get("detected_image_column")
        if image_col and image_col in (result.get("columns") or []):
            try:
                sample_val = preview_slice[0][image_col]
                if isinstance(sample_val, str) and sample_val.startswith(
                    ("http://", "https://")
                ):
                    url_warning = (
                        "This dataset contains image URLs instead of embedded images. "
                        "Images will be downloaded during training, which may be slow for large datasets."
                    )
                    logger.info(f"URL-based image column detected: {image_col}")
                    warning = f"{warning} {url_warning}" if warning else url_warning
            except Exception:
                pass

        return CheckFormatResponse(
            requires_manual_mapping = result["requires_manual_mapping"],
            detected_format = result["detected_format"],
            columns = result["columns"],
            is_image = result.get("is_image", False),
            is_audio = result.get("is_audio", False),
            multimodal_columns = result.get("multimodal_columns"),
            suggested_mapping = result.get("suggested_mapping"),
            detected_image_column = result.get("detected_image_column"),
            detected_audio_column = result.get("detected_audio_column"),
            detected_text_column = result.get("detected_text_column"),
            detected_speaker_column = result.get("detected_speaker_column"),
            preview_samples = preview_samples,
            total_rows = total_rows,
            warning = warning,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking dataset format: {e}", exc_info = True)
        raise HTTPException(
            status_code = 500, detail = f"Failed to check dataset format: {str(e)}"
        )