def module_name_to_file_path(module_name):
    # Avoid importlib machinery as locating a module involves importing its
    # parent, which would trigger import side effects.

    for suffix in [".py", "/__init__.py"]:
        file_path = pathlib.Path(__file__).parents[2] / (
            module_name.replace(".", "/") + suffix
        )
        if file_path.exists():
            return file_path

    raise CodeNotFound