def _load_local_preview_slice(
    *, dataset_path: Path, train_split: str, preview_size: int
):
    from datasets import load_dataset

    if dataset_path.is_dir():
        parquet_dir = (
            dataset_path / "parquet-files"
            if (dataset_path / "parquet-files").exists()
            else dataset_path
        )
        parquet_files = sorted(parquet_dir.glob("*.parquet"))
        if parquet_files:
            dataset = load_dataset(
                "parquet",
                data_files = [str(path) for path in parquet_files],
                split = train_split,
            )
            total_rows = len(dataset)
            preview_slice = dataset.select(range(min(preview_size, total_rows)))
            return preview_slice, total_rows
        else:
            candidate_files: list[Path] = []
            for ext in LOCAL_FILE_EXTS:
                candidate_files.extend(sorted(dataset_path.glob(f"*{ext}")))
            if not candidate_files:
                raise HTTPException(
                    status_code = 400,
                    detail = "Unsupported local dataset directory (expected parquet/json/jsonl/csv files)",
                )
            dataset_path = candidate_files[0]

    if dataset_path.suffix in [".json", ".jsonl"]:
        dataset = load_dataset("json", data_files = str(dataset_path), split = train_split)
    elif dataset_path.suffix == ".csv":
        dataset = load_dataset("csv", data_files = str(dataset_path), split = train_split)
    elif dataset_path.suffix == ".parquet":
        dataset = load_dataset(
            "parquet", data_files = str(dataset_path), split = train_split
        )
    else:
        raise HTTPException(
            status_code = 400, detail = f"Unsupported file format: {dataset_path.suffix}"
        )

    total_rows = len(dataset)
    preview_slice = dataset.select(range(min(preview_size, total_rows)))
    return preview_slice, total_rows