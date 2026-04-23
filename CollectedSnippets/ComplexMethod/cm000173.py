def good_file_paths(top_dir: str = ".") -> Iterator[str]:
    for dir_path, dir_names, filenames in os.walk(top_dir):
        dir_names[:] = [
            d
            for d in dir_names
            if d != "scripts" and d[0] not in "._" and "venv" not in d
        ]
        for filename in filenames:
            if filename == "__init__.py":
                continue
            if os.path.splitext(filename)[1] in (".py", ".ipynb"):
                yield os.path.join(dir_path, filename).lstrip("./")