async def write_file(
    path: str,
    workdir: str,
    workspace_base: str,
    workspace_mount_path_in_sandbox: str,
    content: str,
    start: int = 0,
    end: int = -1,
) -> Observation:
    insert = content.split('\n')

    try:
        whole_path = resolve_path(
            path, workdir, workspace_base, workspace_mount_path_in_sandbox
        )
        if not os.path.exists(os.path.dirname(whole_path)):
            os.makedirs(os.path.dirname(whole_path))
        mode = 'w' if not os.path.exists(whole_path) else 'r+'
        try:
            with open(whole_path, mode, encoding='utf-8') as file:
                if mode != 'w':
                    all_lines = file.readlines()
                    new_file = insert_lines(insert, all_lines, start, end)
                else:
                    new_file = [i + '\n' for i in insert]

                file.seek(0)
                file.writelines(new_file)
                file.truncate()
        except FileNotFoundError:
            return ErrorObservation(f'File not found: {path}')
        except IsADirectoryError:
            return ErrorObservation(
                f'Path is a directory: {path}. You can only write to files'
            )
        except UnicodeDecodeError:
            return ErrorObservation(f'File could not be decoded as utf-8: {path}')
    except PermissionError as e:
        return ErrorObservation(f'Permission error on {path}: {e}')
    return FileWriteObservation(content='', path=path)