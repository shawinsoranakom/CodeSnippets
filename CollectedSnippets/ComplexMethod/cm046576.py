def inspect_seed_dataset(payload: SeedInspectRequest) -> SeedInspectResponse:
    dataset_name = payload.dataset_name.strip()
    if not dataset_name or dataset_name.count("/") < 1:
        raise HTTPException(
            status_code = 400,
            detail = "dataset_name must be a Hugging Face repo id like org/repo",
        )

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise HTTPException(
            status_code = 500, detail = f"seed inspect dependencies unavailable: {exc}"
        ) from exc

    split = _normalize_optional_text(payload.split) or DEFAULT_SPLIT
    subset = _normalize_optional_text(payload.subset)
    token = _normalize_optional_text(payload.hf_token)
    preview_size = int(payload.preview_size)

    preview_rows: list[dict[str, Any]] = []
    data_files = _list_hf_data_files(dataset_name = dataset_name, token = token)

    selected_file = _select_best_file(data_files, split)
    if selected_file:
        try:
            single_file_kwargs = _build_stream_load_kwargs(
                dataset_name = dataset_name,
                split = split,
                subset = subset,
                token = token,
                data_file = selected_file,
            )
            preview_rows = _load_preview_rows(
                load_dataset_fn = load_dataset,
                load_kwargs = single_file_kwargs,
                preview_size = preview_size,
            )
        except (ValueError, OSError, RuntimeError):
            preview_rows = []

    if not preview_rows:
        try:
            split_kwargs = _build_stream_load_kwargs(
                dataset_name = dataset_name,
                split = split,
                subset = subset,
                token = token,
            )
            preview_rows = _load_preview_rows(
                load_dataset_fn = load_dataset,
                load_kwargs = split_kwargs,
                preview_size = preview_size,
            )
        except (ValueError, OSError, RuntimeError) as exc:
            raise HTTPException(
                status_code = 422, detail = f"seed inspect failed: {exc}"
            ) from exc

    if not preview_rows:
        raise HTTPException(
            status_code = 422, detail = "dataset appears empty or unreadable"
        )
    preview_rows = _serialize_preview_rows(preview_rows)
    columns = _extract_columns(preview_rows)

    if not data_files:
        resolved_path = f"datasets/{dataset_name}/**/*.parquet"
    else:
        resolved_path = _resolve_seed_hf_path(dataset_name, data_files, split)
        if not resolved_path:
            raise HTTPException(
                status_code = 422, detail = "unable to resolve seed dataset path"
            )

    return SeedInspectResponse(
        dataset_name = dataset_name,
        resolved_path = resolved_path,
        columns = columns,
        preview_rows = preview_rows,
        split = split,
        subset = subset,
    )