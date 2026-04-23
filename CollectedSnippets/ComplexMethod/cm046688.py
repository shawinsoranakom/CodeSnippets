def _resolve_local_files(file_paths: list) -> list[str]:
        """Resolve a list of local dataset paths to concrete file paths."""
        all_files: list[str] = []
        for dataset_file in file_paths:
            if os.path.isabs(dataset_file):
                file_path = dataset_file
            else:
                file_path = str(resolve_dataset_path(dataset_file))

            file_path_obj = Path(file_path)

            if file_path_obj.is_dir():
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
                all_files.append(str(file_path_obj))
        return all_files