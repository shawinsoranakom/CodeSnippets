def _safe_read_metadata_summary(payload: dict | None) -> dict | None:
    if not payload:
        return None

    actual_num_records = (
        payload.get("actual_num_records")
        if isinstance(payload.get("actual_num_records"), int)
        else None
    )
    target_num_records = (
        payload.get("target_num_records")
        if isinstance(payload.get("target_num_records"), int)
        else actual_num_records
    )

    columns: list[str] | None = None
    schema = payload.get("schema")
    if isinstance(schema, dict):
        columns = [str(key) for key in schema.keys()]
    if not columns:
        stats = payload.get("column_statistics")
        if isinstance(stats, list):
            derived = [
                str(item.get("column_name"))
                for item in stats
                if isinstance(item, dict) and item.get("column_name")
            ]
            columns = derived or None

    parquet_files_count = None
    file_paths = payload.get("file_paths")
    if isinstance(file_paths, dict):
        parquet_files = file_paths.get("parquet-files")
        if isinstance(parquet_files, list):
            parquet_files_count = len(parquet_files)

    total_num_batches = (
        payload.get("total_num_batches")
        if isinstance(payload.get("total_num_batches"), int)
        else parquet_files_count
    )
    num_completed_batches = (
        payload.get("num_completed_batches")
        if isinstance(payload.get("num_completed_batches"), int)
        else total_num_batches
    )

    return {
        "actual_num_records": actual_num_records,
        "target_num_records": target_num_records,
        "total_num_batches": total_num_batches,
        "num_completed_batches": num_completed_batches,
        "columns": columns,
    }