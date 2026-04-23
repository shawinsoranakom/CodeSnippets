def get_path_param_names(path: str) -> set[str]:
    return set(re.findall("{(.*?)}", path))