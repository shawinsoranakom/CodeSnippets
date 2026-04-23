def get_permissions_dict(
    path: str | os.PathLike, renamings=None, ignore=None
) -> dict[str, str]:
    def get_permissions(path: Path) -> str:
        return oct(path.stat().st_mode)

    path_obj = Path(path)

    renamings = renamings or ()
    permissions_dict = {
        ".": get_permissions(path_obj),
    }
    for root, dirs, files in os.walk(path_obj):
        nodes = list(chain(dirs, files))
        if ignore:
            ignored_names = ignore(root, nodes)
            nodes = [node for node in nodes if node not in ignored_names]
        for node in nodes:
            absolute_path = Path(root, node)
            relative_path = str(absolute_path.relative_to(path))
            for search_string, replacement in renamings:
                relative_path = relative_path.replace(search_string, replacement)
            permissions = get_permissions(absolute_path)
            permissions_dict[relative_path] = permissions
    return permissions_dict