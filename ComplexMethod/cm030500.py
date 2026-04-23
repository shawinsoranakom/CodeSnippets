def extract_module_name(filename, path_info):
    """Extract Python module name and type from file path.

    Args:
        filename: Path to the Python file
        path_info: Dictionary from get_python_path_info()

    Returns:
        tuple: (module_name, module_type) where module_type is one of:
               'stdlib', 'site-packages', 'project', or 'other'
    """
    if not filename:
        return ('unknown', 'other')

    try:
        file_path = Path(filename)
    except (ValueError, OSError):
        return (str(filename), 'other')

    # Check if it's in stdlib
    if path_info['stdlib'] and _is_subpath(file_path, path_info['stdlib']):
        try:
            rel_path = file_path.relative_to(path_info['stdlib'])
            return (_path_to_module(rel_path), 'stdlib')
        except ValueError:
            pass

    # Check site-packages
    for site_pkg in path_info['site_packages']:
        if _is_subpath(file_path, site_pkg):
            try:
                rel_path = file_path.relative_to(site_pkg)
                return (_path_to_module(rel_path), 'site-packages')
            except ValueError:
                continue

    # Check other sys.path entries (project files)
    if not str(file_path).startswith(('<', '[')):  # Skip special files
        for path_entry in path_info['sys_path']:
            if _is_subpath(file_path, path_entry):
                try:
                    rel_path = file_path.relative_to(path_entry)
                    return (_path_to_module(rel_path), 'project')
                except ValueError:
                    continue

    # Fallback: just use the filename
    return (_path_to_module(file_path), 'other')