def _get_actual_file(parts):
    for part in parts[1:]:
        if os.path.isfile(part) or os.path.isdir(part):
            return part