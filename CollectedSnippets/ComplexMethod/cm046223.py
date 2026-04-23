def check_cls_dataset(dataset: str | Path, split: str = "") -> dict[str, Any]:
    """Check a classification dataset such as Imagenet.

    This function accepts a `dataset` name and attempts to retrieve the corresponding dataset information. If the
    dataset is not found locally, it attempts to download the dataset from the internet and save it locally.

    Args:
        dataset (str | Path): The name of the dataset.
        split (str, optional): The split of the dataset. Either 'val', 'test', or ''.

    Returns:
        (dict[str, Any]): A dictionary containing the following keys:

            - 'train' (Path): The directory path containing the training set of the dataset.
            - 'val' (Path): The directory path containing the validation set of the dataset.
            - 'test' (Path): The directory path containing the test set of the dataset.
            - 'nc' (int): The number of classes in the dataset.
            - 'names' (dict[int, str]): A dictionary of class names in the dataset.
    """
    # Download (optional if dataset=https://file.zip is passed directly)
    if str(dataset).startswith(("http:/", "https:/")):
        dataset = safe_download(dataset, dir=DATASETS_DIR, unzip=True, delete=False)
    elif str(dataset).endswith((".zip", ".tar", ".gz")):
        file = check_file(dataset)
        dataset = safe_download(file, dir=DATASETS_DIR, unzip=True, delete=False)

    dataset = Path(dataset)
    data_dir = (dataset if dataset.is_dir() else (DATASETS_DIR / dataset)).resolve()
    if not data_dir.is_dir():
        if data_dir.suffix != "":
            raise ValueError(
                f'Classification datasets must be a directory (data="path/to/dir") not a file (data="{dataset}"), '
                "See https://docs.ultralytics.com/datasets/classify/"
            )
        LOGGER.info("")
        LOGGER.warning(f"Dataset not found, missing path {data_dir}, attempting download...")
        t = time.time()
        if str(dataset) == "imagenet":
            subprocess.run(["bash", str(ROOT / "data/scripts/get_imagenet.sh")], check=True)
        else:
            download(f"{ASSETS_URL}/{dataset}.zip", dir=data_dir.parent)
        LOGGER.info(f"Dataset download success ✅ ({time.time() - t:.1f}s), saved to {colorstr('bold', data_dir)}\n")
    train_set = data_dir / "train"
    if not train_set.is_dir():
        LOGGER.warning(f"Dataset 'split=train' not found at {train_set}")
        if image_files := list(data_dir.rglob("*.jpg")) + list(data_dir.rglob("*.png")):
            from ultralytics.data.split import split_classify_dataset

            LOGGER.info(f"Found {len(image_files)} images in subdirectories. Attempting to split...")
            data_dir = split_classify_dataset(data_dir, train_ratio=0.8)
            train_set = data_dir / "train"
        else:
            LOGGER.error(f"No images found in {data_dir} or its subdirectories.")
    val_set = (
        data_dir / "val"
        if (data_dir / "val").exists()
        else data_dir / "validation"
        if (data_dir / "validation").exists()
        else data_dir / "valid"
        if (data_dir / "valid").exists()
        else None
    )  # data/test or data/val
    test_set = data_dir / "test" if (data_dir / "test").exists() else None  # data/val or data/test
    if split == "val" and not val_set:
        LOGGER.warning("Dataset 'split=val' not found, using 'split=test' instead.")
        val_set = test_set
    elif split == "test" and not test_set:
        LOGGER.warning("Dataset 'split=test' not found, using 'split=val' instead.")
        test_set = val_set

    nc = len([x for x in (data_dir / "train").glob("*") if x.is_dir()])  # number of classes
    names = [x.name for x in (data_dir / "train").iterdir() if x.is_dir()]  # class names list
    names = dict(enumerate(sorted(names)))

    # Print to console
    for k, v in {"train": train_set, "val": val_set, "test": test_set}.items():
        prefix = f"{colorstr(f'{k}:')} {v}..."
        if v is None:
            LOGGER.info(prefix)
        else:
            files = [path for path in v.rglob("*.*") if path.suffix[1:].lower() in IMG_FORMATS]
            nf = len(files)  # number of files
            nd = len({file.parent for file in files})  # number of directories
            if nf == 0:
                if k == "train":
                    raise FileNotFoundError(f"{dataset} '{k}:' no training images found")
                else:
                    LOGGER.warning(f"{prefix} found {nf} images in {nd} classes (no images found)")
            elif nd != nc:
                LOGGER.error(f"{prefix} found {nf} images in {nd} classes (requires {nc} classes, not {nd})")
            else:
                LOGGER.info(f"{prefix} found {nf} images in {nd} classes ✅ ")

    return {"train": train_set, "val": val_set, "test": test_set, "nc": nc, "names": names, "channels": 3}