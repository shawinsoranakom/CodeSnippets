def split_json_by_tp_pp(
    input_file: str = "benchmark_results.json", output_root: str = "."
) -> list[str]:
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        for key in ("results", "serving_results", "benchmarks", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break

    df = pd.DataFrame(data)

    name_col = next(
        (c for c in ["Test name", "test_name", "Test Name"] if c in df.columns), None
    )
    if name_col:
        df = df[
            df[name_col].astype(str).str.contains(r"serving", case=False, na=False)
        ].copy()

    rename_map = {
        "tp_size": "TP Size",
        "tensor_parallel_size": "TP Size",
        "pp_size": "PP Size",
        "pipeline_parallel_size": "PP Size",
    }
    df.rename(
        columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True
    )

    if "TP Size" not in df.columns:
        df["TP Size"] = 1
    if "PP Size" not in df.columns:
        df["PP Size"] = 1

    df["TP Size"] = pd.to_numeric(df["TP Size"], errors="coerce").fillna(1).astype(int)
    df["PP Size"] = pd.to_numeric(df["PP Size"], errors="coerce").fillna(1).astype(int)

    saved_paths: list[str] = []
    for (tp, pp), group_df in df.groupby(["TP Size", "PP Size"], dropna=False):
        folder_name = os.path.join(output_root, f"tp{int(tp)}_pp{int(pp)}")
        os.makedirs(folder_name, exist_ok=True)
        filepath = os.path.join(folder_name, "benchmark_results.json")
        group_df.to_json(filepath, orient="records", indent=2, force_ascii=False)
        print(f"Saved: {filepath}")
        saved_paths.append(filepath)

    return saved_paths