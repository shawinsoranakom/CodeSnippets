def get_new_command(command):
    destination = _get_destination(command)
    paths = _get_all_absolute_paths_from_history(command)

    return [replace_argument(command.script, destination, path)
            for path in paths if path.endswith(destination)
            and Path(path).expanduser().exists()]