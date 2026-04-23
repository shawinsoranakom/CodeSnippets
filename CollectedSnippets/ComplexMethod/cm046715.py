def convert_sharegpt_with_images_to_vlm_format(
    dataset,
    image_column = "image",
    messages_column = "conversations",
    dataset_name = None,
    progress_callback = None,
):
    """
    Converts ShareGPT/ChatML datasets that have a separate image column and
    ``<image>`` placeholders inside the conversation text.

    Example input::

        {
            "image": "sam/images/sa_545504.jpg",
            "conversations": [
                {"from": "human", "value": "<image>\\nWhat is this photo about?"},
                {"from": "gpt",   "value": "The image captures..."}
            ]
        }

    Returns a list of dicts in standard VLM messages format (PIL Images inline).
    """
    from PIL import Image
    from tqdm import tqdm

    _IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff")
    _ROLE_MAP = {
        "human": "user",
        "user": "user",
        "gpt": "assistant",
        "assistant": "assistant",
        "system": "system",
    }

    def _notify(msg):
        if progress_callback:
            progress_callback(status_message = msg)

    # ── Resolve image loading strategy (same 3-tier as convert_to_vlm_format) ──
    total = len(dataset)
    first_image = next(iter(dataset))[image_column]

    _image_lookup = None
    if (
        isinstance(first_image, str)
        and not first_image.startswith(("http://", "https://"))
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
            # Also add the full relative paths as keys (for paths like "sam/images/sa_545504.jpg")
            for f in repo_files:
                if any(f.lower().endswith(ext) for ext in _IMAGE_EXTS):
                    _image_lookup[f] = f
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

    def _resolve_image(image_data):
        """Resolve image data to a PIL Image object."""
        if hasattr(image_data, "size") and hasattr(image_data, "mode"):
            return image_data  # Already PIL
        if isinstance(image_data, str):
            if image_data.startswith(("http://", "https://")):
                import fsspec
                from io import BytesIO

                with fsspec.open(image_data, "rb", expand = True) as f:
                    return Image.open(BytesIO(f.read())).convert("RGB")
            elif _image_lookup is not None and image_data in _image_lookup:
                from huggingface_hub import hf_hub_download

                local_path = hf_hub_download(
                    dataset_name,
                    _image_lookup[image_data],
                    repo_type = "dataset",
                )
                return Image.open(local_path).convert("RGB")
            else:
                return Image.open(image_data).convert("RGB")
        if isinstance(image_data, dict) and (
            "bytes" in image_data or "path" in image_data
        ):
            if image_data.get("bytes"):
                from io import BytesIO

                return Image.open(BytesIO(image_data["bytes"])).convert("RGB")
            if image_data.get("path"):
                return Image.open(image_data["path"]).convert("RGB")
        raise ValueError(f"Cannot resolve image: {type(image_data)}")

    def _convert_single_sample(sample):
        """Convert a single ShareGPT+image sample to standard VLM format."""
        pil_image = _resolve_image(sample[image_column])
        conversation = sample[messages_column]

        new_messages = []
        for msg in conversation:
            role_raw = msg.get("from") or msg.get("role", "user")
            role = _ROLE_MAP.get(role_raw.lower(), role_raw.lower())
            text = msg.get("value") or msg.get("content") or ""

            # Split on <image> to interleave text and image content blocks
            if "<image>" in text:
                parts = text.split("<image>")
                content = []
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        content.append({"type": "text", "text": part})
                    if i < len(parts) - 1:
                        content.append({"type": "image", "image": pil_image})
                # If <image> was the entire text, content might just be the image
                if not content:
                    content.append({"type": "image", "image": pil_image})
            else:
                content = [{"type": "text", "text": text}]

            new_messages.append({"role": role, "content": content})

        return {"messages": new_messages}

    # ── Full conversion with progress ──
    logger.info(f"🔄 Converting {total} samples from ShareGPT+image format...")
    converted_list = []
    failed_count = 0

    pbar = tqdm(dataset, total = total, desc = "Converting ShareGPT+image", unit = "sample")
    for sample in pbar:
        try:
            converted_list.append(_convert_single_sample(sample))
        except Exception as e:
            failed_count += 1
            if failed_count == 1:
                logger.info(f"⚠️ First conversion failure: {type(e).__name__}: {e}")
        pbar.set_postfix(ok = len(converted_list), failed = failed_count, refresh = False)
    pbar.close()

    if failed_count > 0:
        logger.info(
            f"⚠️ Skipped {failed_count}/{total} ({failed_count*100//total}%) samples"
        )

    if len(converted_list) == 0:
        raise ValueError(
            f"All {total} samples failed during ShareGPT+image conversion — "
            "no usable samples found."
        )

    logger.info(f"✅ Converted {len(converted_list)}/{total} samples")
    _notify(f"Converted {len(converted_list):,}/{total:,} samples successfully")
    return converted_list