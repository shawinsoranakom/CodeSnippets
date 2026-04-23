def collect_models_files() -> list[str]:
    out: list[str] = []
    for folder_name, bases in get_comfy_models_folders():
        rel_files = folder_paths.get_filename_list(folder_name) or []
        for rel_path in rel_files:
            if not all(is_visible(part) for part in Path(rel_path).parts):
                continue
            abs_path = folder_paths.get_full_path(folder_name, rel_path)
            if not abs_path:
                continue
            abs_path = os.path.abspath(abs_path)
            allowed = False
            abs_p = Path(abs_path)
            for b in bases:
                if abs_p.is_relative_to(os.path.abspath(b)):
                    allowed = True
                    break
            if allowed:
                out.append(abs_path)
    return out