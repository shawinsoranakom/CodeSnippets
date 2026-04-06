def _get_all_absolute_paths_from_history(command):
    counter = Counter()

    for line in get_valid_history_without_current(command):
        splitted = shell.split_command(line)

        for param in splitted[1:]:
            if param.startswith('/') or param.startswith('~'):
                if param.endswith('/'):
                    param = param[:-1]

                counter[param] += 1

    return (path for path, _ in counter.most_common(None))