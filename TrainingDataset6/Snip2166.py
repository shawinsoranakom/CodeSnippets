def _get_actual_scm():
    for path, scm in path_to_scm.items():
        if Path(path).is_dir():
            return scm