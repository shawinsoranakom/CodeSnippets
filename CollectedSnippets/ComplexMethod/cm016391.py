def _collect_output_absolute_paths(history_result: dict) -> list[str]:
    """Extract absolute file paths for output items from a history result."""
    paths: list[str] = []
    seen: set[str] = set()
    for node_output in history_result.get("outputs", {}).values():
        for items in node_output.values():
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type not in ("output", "temp"):
                    continue
                base_dir = folder_paths.get_directory_by_type(item_type)
                if base_dir is None:
                    continue
                base_dir = os.path.abspath(base_dir)
                filename = item.get("filename")
                if not filename:
                    continue
                abs_path = os.path.abspath(
                    os.path.join(base_dir, item.get("subfolder", ""), filename)
                )
                if not abs_path.startswith(base_dir + os.sep) and abs_path != base_dir:
                    continue
                if abs_path not in seen:
                    seen.add(abs_path)
                    paths.append(abs_path)
    return paths