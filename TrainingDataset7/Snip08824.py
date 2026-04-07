def get_relative_path(path):
        try:
            migration_string = os.path.relpath(path)
        except ValueError:
            migration_string = path
        if migration_string.startswith(".."):
            migration_string = path
        return migration_string