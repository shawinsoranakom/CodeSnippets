def get_asset_category_and_relative_path(
    file_path: str,
) -> tuple[Literal["input", "output", "temp", "models"], str]:
    """Determine which root category a file path belongs to.

    Categories:
      - 'input': under folder_paths.get_input_directory()
      - 'output': under folder_paths.get_output_directory()
      - 'temp': under folder_paths.get_temp_directory()
      - 'models': under any base path from get_comfy_models_folders()

    Returns:
        (root_category, relative_path_inside_that_root)

    Raises:
        ValueError: path does not belong to any known root.
    """
    fp_abs = os.path.abspath(file_path)

    def _check_is_within(child: str, parent: str) -> bool:
        return Path(child).is_relative_to(parent)

    def _compute_relative(child: str, parent: str) -> str:
        # Normalize relative path, stripping any leading ".." components
        # by anchoring to root (os.sep) then computing relpath back from it.
        return os.path.relpath(
            os.path.join(os.sep, os.path.relpath(child, parent)), os.sep
        )

    # 1) input
    input_base = os.path.abspath(folder_paths.get_input_directory())
    if _check_is_within(fp_abs, input_base):
        return "input", _compute_relative(fp_abs, input_base)

    # 2) output
    output_base = os.path.abspath(folder_paths.get_output_directory())
    if _check_is_within(fp_abs, output_base):
        return "output", _compute_relative(fp_abs, output_base)

    # 3) temp
    temp_base = os.path.abspath(folder_paths.get_temp_directory())
    if _check_is_within(fp_abs, temp_base):
        return "temp", _compute_relative(fp_abs, temp_base)

    # 4) models (check deepest matching base to avoid ambiguity)
    best: tuple[int, str, str] | None = None  # (base_len, bucket, rel_inside_bucket)
    for bucket, bases in get_comfy_models_folders():
        for b in bases:
            base_abs = os.path.abspath(b)
            if not _check_is_within(fp_abs, base_abs):
                continue
            cand = (len(base_abs), bucket, _compute_relative(fp_abs, base_abs))
            if best is None or cand[0] > best[0]:
                best = cand

    if best is not None:
        _, bucket, rel_inside = best
        combined = os.path.join(bucket, rel_inside)
        return "models", os.path.relpath(os.path.join(os.sep, combined), os.sep)

    raise ValueError(
        f"Path is not within input, output, temp, or configured model bases: {file_path}"
    )