async def convert_ndjson_to_yolo(ndjson_path: str | Path, output_path: str | Path | None = None) -> Path:
    """Convert NDJSON dataset format to Ultralytics YOLO dataset structure.

    This function converts datasets stored in NDJSON (Newline Delimited JSON) format to the standard YOLO format. For
    detection/segmentation/pose/obb tasks, it creates separate directories for images and labels. For classification
    tasks, it creates the ImageNet-style {split}/{class_name}/ folder structure. It supports parallel processing for
    efficient conversion of large datasets and can download images from URLs.

    The NDJSON format consists of:
    - First line: Dataset metadata with class names, task type, and configuration
    - Subsequent lines: Individual image records with annotations and optional URLs

    Args:
        ndjson_path (str | Path): Path to the input NDJSON file containing dataset information.
        output_path (str | Path | None, optional): Directory where the converted YOLO dataset will be saved. If None,
            uses the DATASETS_DIR directory. Defaults to None.

    Returns:
        (Path): Path to the generated data.yaml file (detection) or dataset directory (classification).

    Examples:
        Convert a local NDJSON file:
        >>> yaml_path = await convert_ndjson_to_yolo("dataset.ndjson")
        >>> print(f"Dataset converted to: {yaml_path}")

        Convert with custom output directory:
        >>> yaml_path = await convert_ndjson_to_yolo("dataset.ndjson", output_path="./converted_datasets")

        Use with YOLO training
        >>> from ultralytics import YOLO
        >>> model = YOLO("yolo26n.pt")
        >>> model.train(data="https://github.com/ultralytics/assets/releases/download/v0.0.0/coco8-ndjson.ndjson")
    """
    from ultralytics.utils.checks import check_requirements

    check_requirements("aiohttp")
    import aiohttp

    ndjson_path = Path(check_file(ndjson_path))
    output_path = Path(output_path or DATASETS_DIR)
    with open(ndjson_path) as f:
        lines = [json.loads(line.strip()) for line in f if line.strip()]
    dataset_record, image_records = lines[0], lines[1:]

    # Hash stable content plus source identity. Query strings are excluded because signed URLs change on every export.
    _h = hashlib.sha256()
    for r in lines:
        hash_record = {k: v for k, v in r.items() if k != "url"}
        if r.get("file"):
            hash_record["_source"] = clean_url(r["url"]) if r.get("url") else str(ndjson_path.parent.resolve())
        _h.update(json.dumps(hash_record, sort_keys=True).encode())
    _hash = _h.hexdigest()[:8]

    # Hash-qualified dirs allow identical datasets to reuse downloads while preventing changed datasets from mutating
    # files that another training job may still be reading.
    dataset_dir = output_path / f"{ndjson_path.stem}-{_hash}"
    yaml_path = dataset_dir / "data.yaml"
    if yaml_path.is_file():
        try:
            cached = YAML.load(yaml_path)
            if cached.get("hash") == _hash and all(
                (dataset_dir / cached[split]).is_dir() and (dataset_dir / "labels" / split).is_dir()
                for split in ("train", "val", "test")
                if split in cached
            ):
                return yaml_path
        except Exception:
            pass
    splits = {record["split"] for record in image_records}

    # Check if this is a classification dataset
    is_classification = dataset_record.get("task") == "classify"
    class_names = {int(k): v for k, v in dataset_record.get("class_names", {}).items()}
    inferred_nc = None

    # Validate required fields before downloading images
    task = dataset_record.get("task", "detect")
    if not is_classification:
        class_ids = {
            int(label[0])
            for record in image_records
            for labels in record.get("annotations", {}).values()
            for label in labels
            if label
        }
        if class_ids or class_names:
            max_class_id = max(class_ids | set(class_names))
            if class_names:
                for i in range(max_class_id + 1):
                    class_names.setdefault(i, f"class{i}")
            else:
                inferred_nc = max_class_id + 1
    if not is_classification:
        if "train" not in splits:
            raise ValueError(f"Dataset missing required 'train' split. Found splits: {sorted(splits)}")
        if "val" not in splits:
            train_records = [r for r in image_records if r.get("split") == "train"]
            if len(train_records) < 2:
                raise ValueError(
                    f"Dataset has only {len(train_records)} image(s) and no 'val' split. "
                    f"Need at least 2 images to auto-split into train/val."
                )
            random.Random(0).shuffle(train_records)  # local RNG to avoid mutating global training seed
            val_count = max(1, len(train_records) // 10)
            for r in train_records[:val_count]:
                r["split"] = "val"
            splits.add("val")
            LOGGER.warning(
                f"WARNING ⚠️ No 'val' split found in dataset. "
                f"Auto-splitting {len(train_records)} images into {len(train_records) - val_count} train, {val_count} val. "
                f"For best results, manually assign validation images in Platform dataset page."
            )
    if task == "pose" and "kpt_shape" not in dataset_record:
        dataset_record["kpt_shape"] = _infer_ndjson_kpt_shape(image_records)

    # Check if dataset already exists (enables image reuse across split changes)
    _reuse = dataset_dir.exists()
    if _reuse:
        yaml_path.unlink(missing_ok=True)  # Invalidate hash before destructive ops (crash safety)
        if not is_classification:
            shutil.rmtree(dataset_dir / "labels", ignore_errors=True)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    data_yaml = None

    if not is_classification:
        # Detection/segmentation/pose/obb: prepare YAML and create base structure
        data_yaml = dict(dataset_record)
        if class_names:
            data_yaml["names"] = class_names
        elif inferred_nc is not None:
            data_yaml["nc"] = inferred_nc
        data_yaml.pop("class_names", None)
        data_yaml.pop("type", None)  # Remove NDJSON-specific fields
        for split in sorted(splits):
            (dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
            data_yaml[split] = f"images/{split}"

    async def process_record(session, semaphore, record):
        """Process single image record with async session."""
        async with semaphore:
            split, original_name = record["split"], record["file"]
            annotations = record.get("annotations", {})

            if is_classification:
                # Classification: place image in {split}/{class_name}/ folder
                class_ids = annotations.get("classification", [])
                class_id = class_ids[0] if class_ids else 0
                class_name = class_names.get(class_id, str(class_id))
                image_path = dataset_dir / split / class_name / original_name
            else:
                # Detection: write label file and place image in images/{split}/
                image_path = dataset_dir / "images" / split / original_name
                label_path = dataset_dir / "labels" / split / f"{Path(original_name).stem}.txt"
                lines_to_write = []
                for key in annotations.keys():
                    lines_to_write = [" ".join(map(str, item)) for item in annotations[key]]
                    break
                label_path.write_text("\n".join(lines_to_write) + "\n" if lines_to_write else "")

            # Reuse existing image from another split dir (avoids redownload on resplit) or download
            if not image_path.exists():
                if _reuse:
                    for s in ("train", "val", "test"):
                        if s == split:
                            continue
                        candidate = (
                            (dataset_dir / s / class_name / original_name)
                            if is_classification
                            else (dataset_dir / "images" / s / original_name)
                        )
                        if candidate.exists():
                            image_path.parent.mkdir(parents=True, exist_ok=True)
                            candidate.rename(image_path)
                            break
                if not image_path.exists() and (http_url := record.get("url")):
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    # Retry with exponential backoff (3 attempts: 1s, 2s delays before the final attempt)
                    for attempt in range(3):
                        error = None
                        try:
                            async with session.get(http_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                                response.raise_for_status()
                                image_path.write_bytes(await response.read())
                            return True
                        except aiohttp.ClientResponseError as e:
                            error = e
                            if e.status not in {408, 429} and e.status < 500:
                                LOGGER.warning(f"Failed to download {http_url}: {e}")
                                return False
                        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                            error = e
                        except Exception as e:  # OSError, disk full, permissions — not transient, don't retry
                            LOGGER.warning(f"Failed to save {http_url}: {e}")
                            return False
                        if attempt < 2:  # Don't sleep after last attempt
                            await asyncio.sleep(2**attempt)  # 1s, 2s backoff
                        else:
                            LOGGER.warning(f"Failed to download {http_url} after 3 attempts: {error}")
                            return False
            return True

    # Process all images with async downloads (limit connections for small datasets)
    semaphore = asyncio.Semaphore(min(128, len(image_records)))
    async with aiohttp.ClientSession() as session:
        pbar = TQDM(
            total=len(image_records),
            desc=f"Converting {ndjson_path.name} → {dataset_dir} ({len(image_records)} images)",
        )

        async def tracked_process(record):
            result = await process_record(session, semaphore, record)
            pbar.update(1)
            return result

        results = await asyncio.gather(*[tracked_process(record) for record in image_records])
        pbar.close()

    # Validate images were downloaded successfully
    success_count = sum(1 for r in results if r)
    if success_count == 0:
        raise RuntimeError(f"Failed to download any images from {ndjson_path}. Check network connection and URLs.")
    if success_count < len(image_records):
        LOGGER.warning(f"Downloaded {success_count}/{len(image_records)} images from {ndjson_path}")

    # Remove orphaned images no longer in the dataset (prevents stale background images in training)
    if _reuse:
        expected_paths = set()
        for r in image_records:
            s, name = r["split"], r["file"]
            if is_classification:
                ann = r.get("annotations", {})
                cids = ann.get("classification", [])
                cid = cids[0] if cids else 0
                expected_paths.add(dataset_dir / s / class_names.get(cid, str(cid)) / name)
            else:
                expected_paths.add(dataset_dir / "images" / s / name)
        img_root = dataset_dir if is_classification else (dataset_dir / "images")
        for p in img_root.rglob("*"):
            if p.is_file() and p not in expected_paths:
                p.unlink()

    if is_classification:
        # Classification: return dataset directory (check_cls_dataset expects a directory path)
        return dataset_dir
    else:
        # Detection: write data.yaml with hash for future change detection
        data_yaml["hash"] = _hash
        YAML.save(yaml_path, data_yaml)
        return yaml_path