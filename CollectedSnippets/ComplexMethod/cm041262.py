def extract_from_jsonpointer_path(target, path: str, delimiter: str = "/", auto_create=False):
    parts = path.strip(delimiter).split(delimiter)
    for part in parts:
        path_part = int(part) if is_number(part) else part
        if isinstance(target, list) and not is_number(path_part):
            if path_part == "-":
                # special case where path is like /path/to/list/- where "/-" means "append to list"
                continue
            LOG.warning('Attempting to extract non-int index "%s" from list: %s', path_part, target)
            return None
        target_new = target[path_part] if isinstance(target, list) else target.get(path_part)
        if target_new is None:
            if not auto_create:
                return
            target[path_part] = target_new = {}
        target = target_new
    return target