def get_full_name(path: str, prefixes: dict[str, bool], extensions: tuple[str] | None = None) -> str | None:
    """Return the full name of the plugin at the given path by matching against the given path prefixes, or None if no match is found."""
    for prefix, flat in prefixes.items():
        if path.startswith(prefix):
            relative_path = os.path.relpath(path, prefix)

            if flat:
                full_name = os.path.basename(relative_path)
            else:
                full_name = relative_path

            full_name, file_ext = os.path.splitext(full_name)

            name = os.path.basename(full_name)

            if name == '__init__':
                return None

            if extensions and file_ext not in extensions:
                return None

            if name.startswith('_'):
                name = name[1:]

            full_name = os.path.join(os.path.dirname(full_name), name).replace(os.path.sep, '.')

            return full_name

    return None