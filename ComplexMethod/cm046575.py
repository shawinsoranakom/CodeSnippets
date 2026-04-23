def _read_preview_rows_from_local_file(
    path: Path, preview_size: int
) -> list[dict[str, Any]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise HTTPException(
            status_code = 500, detail = f"seed inspect dependencies unavailable: {exc}"
        ) from exc

    ext = path.suffix.lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(path, nrows = preview_size, encoding = "utf-8-sig")
            df.columns = df.columns.str.strip()
            unnamed = [c for c in df.columns if c == "" or c.startswith("Unnamed:")]
            if unnamed:
                df = df.drop(columns = unnamed)
                full_df = pd.read_csv(path, encoding = "utf-8-sig")
                full_df.columns = full_df.columns.str.strip()
                full_df = full_df.drop(columns = unnamed)
                tmp_csv = path.with_suffix(".tmp.csv")
                full_df.to_csv(tmp_csv, index = False, encoding = "utf-8")
                tmp_csv.replace(path)
        elif ext == ".jsonl":
            df = pd.read_json(path, lines = True).head(preview_size)
        elif ext == ".json":
            try:
                df = pd.read_json(path).head(preview_size)
            except ValueError:
                df = pd.read_json(path, lines = True).head(preview_size)
        else:
            raise HTTPException(status_code = 422, detail = f"unsupported file type: {ext}")
    except HTTPException:
        raise
    except (ValueError, OSError) as exc:
        raise HTTPException(
            status_code = 422, detail = f"seed inspect failed: {exc}"
        ) from exc

    rows = df.to_dict(orient = "records")
    return _serialize_preview_rows(rows)