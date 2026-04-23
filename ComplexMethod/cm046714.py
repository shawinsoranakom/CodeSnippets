def convert_to_vlm_format(
    dataset,
    instruction = None,
    text_column = "text",
    image_column = "image",
    dataset_name = None,
    progress_callback = None,
):
    """
    Converts simple {image, text} format to VLM messages format.

    Returns a LIST, not a HuggingFace Dataset (to preserve PIL Images).

    For URL-based image datasets, runs a 200-sample parallel probe first to
    estimate download speed and failure rate, then reports time estimate or
    warning through progress_callback before proceeding with the full conversion.

    Args:
        progress_callback: Optional callable(status_message=str) to report
                          progress to the training overlay.

    Returns:
        list: List of dicts with 'messages' field
    """
    from PIL import Image
    from .vlm_processing import generate_smart_vlm_instruction

    def _notify(msg):
        """Send status update to the training overlay if callback is available."""
        if progress_callback:
            progress_callback(status_message = msg)

    # Generate smart instruction if not provided
    if instruction is None:
        instruction_info = generate_smart_vlm_instruction(
            dataset,
            text_column = text_column,
            image_column = image_column,
            dataset_name = dataset_name,
        )

        instruction = instruction_info["instruction"]
        instruction_column = instruction_info.get("instruction_column")
        uses_dynamic = instruction_info["uses_dynamic_instruction"]

        logger.info(
            f"📝 Auto-detected instruction type: {instruction_info['instruction_type']}"
        )
        logger.info(f"📝 Confidence: {instruction_info['confidence']:.2f}")
        if not uses_dynamic:
            logger.info(f"📝 Using instruction: '{instruction}'")
        else:
            logger.info(
                f"📝 Using dynamic instructions from column: '{instruction_column}'"
            )
    else:
        instruction_column = None
        uses_dynamic = False

    def _convert_single_sample(sample):
        """Convert a single sample to VLM format."""
        # Get image (might be PIL Image, local path, URL, or bare filename)
        image_data = sample[image_column]

        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                import fsspec
                from io import BytesIO

                with fsspec.open(image_data, "rb", expand = True) as f:
                    image_data = Image.open(BytesIO(f.read())).convert("RGB")
            elif _image_lookup is not None and image_data in _image_lookup:
                # Bare filename → resolve via HF repo lookup
                from huggingface_hub import hf_hub_download

                local_path = hf_hub_download(
                    dataset_name,
                    _image_lookup[image_data],
                    repo_type = "dataset",
                )
                image_data = Image.open(local_path).convert("RGB")
            else:
                image_data = Image.open(image_data).convert("RGB")

        # Get text (if list of strings, pick a random one — e.g. multiple captions)
        text_data = sample[text_column]
        if isinstance(text_data, list) and len(text_data) > 0:
            import random

            text_data = random.choice(text_data)

        # Get instruction (static or dynamic)
        if uses_dynamic and instruction_column:
            current_instruction = sample[instruction_column]
        else:
            current_instruction = instruction

        # Build VLM messages - simple structure
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": current_instruction},
                    {"type": "image", "image": image_data},  # PIL object
                ],
            },
            {"role": "assistant", "content": [{"type": "text", "text": text_data}]},
        ]

        # Return dict with messages
        return {"messages": messages}

    total = len(dataset)
    first_image = next(iter(dataset))[image_column]
    has_urls = isinstance(first_image, str) and first_image.startswith(
        ("http://", "https://")
    )

    # ── Bare-filename detection: images stored as filenames (e.g. "img_001.png")
    #    that don't exist locally.  Build a basename→repo_path lookup so we can
    #    resolve them via hf_hub_download during conversion.
    _image_lookup = None
    _IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")
    if (
        not has_urls
        and isinstance(first_image, str)
        and not os.path.exists(first_image)
        and dataset_name
    ):
        try:
            from huggingface_hub import HfApi

            _notify("Resolving image filenames from HF repo...")
            logger.info(
                f"🔍 Image column contains bare filenames (e.g. '{first_image}') — building repo lookup..."
            )
            repo_files = HfApi().list_repo_files(dataset_name, repo_type = "dataset")
            _image_lookup = {
                os.path.basename(f): f
                for f in repo_files
                if any(f.lower().endswith(ext) for ext in _IMAGE_EXTS)
            }
            if first_image in _image_lookup:
                logger.info(
                    f"✅ Matched {len(_image_lookup)} image files in repo (e.g. '{first_image}' → '{_image_lookup[first_image]}')"
                )
            else:
                logger.info(
                    f"⚠️ Built lookup with {len(_image_lookup)} images but '{first_image}' not found — falling back to local open"
                )
                _image_lookup = None
        except Exception as e:
            logger.info(f"⚠️ Failed to build HF repo image lookup: {e}")
            _image_lookup = None

    # ── URL probe: 200 samples with parallel workers to estimate speed + failure rate ──
    PROBE_SIZE = 200
    MAX_FAIL_RATE = 0.3

    if has_urls and total > PROBE_SIZE:
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from utils.hardware import safe_thread_num_proc

        num_workers = safe_thread_num_proc()
        _notify(f"Probing {PROBE_SIZE} image URLs with {num_workers} workers...")
        logger.info(
            f"🔍 Probing {PROBE_SIZE}/{total} image URLs with {num_workers} workers..."
        )

        probe_samples = [dataset[i] for i in range(PROBE_SIZE)]
        probe_ok = 0
        probe_fail = 0
        probe_start = time.time()

        with ThreadPoolExecutor(max_workers = num_workers) as executor:
            futures = {
                executor.submit(_convert_single_sample, s): s for s in probe_samples
            }
            for future in as_completed(futures):
                try:
                    future.result()
                    probe_ok += 1
                except Exception:
                    probe_fail += 1

        probe_elapsed = time.time() - probe_start
        probe_total = probe_ok + probe_fail
        fail_rate = probe_fail / probe_total if probe_total > 0 else 0
        throughput = probe_total / probe_elapsed if probe_elapsed > 0 else 0

        if fail_rate >= MAX_FAIL_RATE:
            issues = [
                f"{fail_rate:.0%} of the first {PROBE_SIZE} image URLs failed to download ({probe_fail}/{probe_total})",
                "Images are external URLs, not embedded in the dataset",
            ]
            # Try LLM-friendly warning
            friendly = None
            try:
                from .llm_assist import llm_generate_dataset_warning

                friendly = llm_generate_dataset_warning(
                    issues,
                    dataset_name = dataset_name,
                    modality = "vision",
                    column_names = [image_column, text_column],
                )
            except Exception:
                pass
            msg = friendly or (
                f"⚠️ {fail_rate:.0%} of the first {PROBE_SIZE} images failed to download "
                f"({probe_fail}/{probe_total}). "
                "This dataset has too many broken or unreachable image URLs. "
                "Consider using a dataset with embedded images instead."
            )
            logger.info(msg)
            _notify(msg)
            raise ValueError(msg)

        # Estimate total time for remaining samples
        remaining = total - PROBE_SIZE
        estimated_seconds = remaining / throughput if throughput > 0 else 0
        eta_str = _format_eta(estimated_seconds)

        info_msg = (
            f"Downloading {total:,} images ({num_workers} workers, ~{throughput:.1f} img/s). "
            f"Estimated time: ~{eta_str}"
        )
        if probe_fail > 0:
            info_msg += f" | {fail_rate:.0%} broken URLs will be skipped"

        logger.info(
            f"✅ Probe passed: {probe_ok}/{probe_total} ok, {probe_fail} failed ({fail_rate:.0%}), {throughput:.1f} img/s"
        )
        logger.info(f"⏱️ Estimated time for {total:,} samples: ~{eta_str}")
        _notify(info_msg)

    # ── Full conversion with progress ──
    from tqdm import tqdm

    logger.info(f"🔄 Converting {total} samples to VLM format...")
    converted_list = []
    failed_count = 0

    if has_urls:
        # Parallel conversion for URL-based datasets
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from utils.hardware import safe_thread_num_proc

        num_workers = safe_thread_num_proc()
        batch_size = 500
        start_time = time.time()

        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_samples = [dataset[i] for i in range(batch_start, batch_end)]

            with ThreadPoolExecutor(max_workers = num_workers) as executor:
                futures = {
                    executor.submit(_convert_single_sample, s): i
                    for i, s in enumerate(batch_samples)
                }
                batch_results = [None] * len(batch_samples)
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        batch_results[idx] = future.result()
                    except Exception as e:
                        failed_count += 1
                        if failed_count == 1:
                            logger.info(
                                f"First VLM conversion failure: {type(e).__name__}: {e}"
                            )

            converted_list.extend(r for r in batch_results if r is not None)

            # Progress update every batch
            elapsed = time.time() - start_time
            done = batch_end
            rate = done / elapsed if elapsed > 0 else 0
            remaining_time = (total - done) / rate if rate > 0 else 0
            eta_str = _format_eta(remaining_time)
            progress_msg = f"Downloading images: {done:,}/{total:,} ({done*100//total}%) | ~{eta_str} remaining | {failed_count} skipped"
            logger.info(
                f"  [{done}/{total}] {rate:.1f} img/s, {failed_count} failed, ETA {eta_str}"
            )
            _notify(progress_msg)
    else:
        # Sequential conversion for local/embedded images (fast, no I/O bottleneck)
        pbar = tqdm(dataset, total = total, desc = "Converting VLM samples", unit = "sample")
        for sample in pbar:
            try:
                converted_list.append(_convert_single_sample(sample))
            except Exception as e:
                failed_count += 1
                if failed_count == 1:
                    # Log the first failure to aid debugging
                    logger.info(
                        f"First VLM conversion failure: {type(e).__name__}: {e}"
                    )
            pbar.set_postfix(ok = len(converted_list), failed = failed_count, refresh = False)
        pbar.close()

    if failed_count > 0:
        fail_rate = failed_count / total
        logger.info(
            f"⚠️ Skipped {failed_count}/{total} ({fail_rate:.0%}) samples with broken/unreachable images"
        )
        # For datasets that skipped the probe (small URL datasets), check fail rate now
        if has_urls and fail_rate >= MAX_FAIL_RATE:
            issues = [
                f"{fail_rate:.0%} of images failed to download ({failed_count}/{total})",
                "Images are external URLs, not embedded in the dataset",
            ]
            friendly = None
            try:
                from .llm_assist import llm_generate_dataset_warning

                friendly = llm_generate_dataset_warning(
                    issues,
                    dataset_name = dataset_name,
                    modality = "vision",
                    column_names = [image_column, text_column],
                )
            except Exception:
                pass
            msg = friendly or (
                f"⚠️ {fail_rate:.0%} of images failed to download ({failed_count}/{total}). "
                "This dataset has too many broken or unreachable image URLs. "
                "Consider using a dataset with embedded images instead."
            )
            _notify(msg)
            raise ValueError(msg)

    if len(converted_list) == 0:
        issues = [
            f"All {total} samples failed during VLM conversion — no usable images found",
            f"Image column '{image_column}' may contain URLs that are no longer accessible, "
            "or local file paths that don't exist",
        ]
        friendly = None
        try:
            from .llm_assist import llm_generate_dataset_warning

            friendly = llm_generate_dataset_warning(
                issues,
                dataset_name = dataset_name,
                modality = "vision",
                column_names = [image_column, text_column],
            )
        except Exception:
            pass
        raise ValueError(
            friendly
            or (
                f"All {total} samples failed during VLM conversion — no usable images found. "
                "This dataset may contain only image URLs that are no longer accessible."
            )
        )

    logger.info(f"✅ Converted {len(converted_list)}/{total} samples")
    _notify(f"Converted {len(converted_list):,}/{total:,} images successfully")

    # Return list, NOT Dataset
    return converted_list