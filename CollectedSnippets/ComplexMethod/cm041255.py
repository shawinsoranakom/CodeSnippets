def rm_rf(path: str) -> None:
    """
    Recursively removes a file or directory
    """
    from localstack.utils.platform import is_debian
    from localstack.utils.run import run

    if not path or not os.path.exists(path):
        return
    # Running the native command can be an order of magnitude faster in Alpine on Travis-CI
    if is_debian():
        try:
            return run(f'rm -rf "{path}"')  # type: ignore[return-value]
        except Exception:
            pass
    # Make sure all files are writeable and dirs executable to remove
    try:
        chmod_r(path, 0o777)
    except PermissionError:
        pass  # todo log
    # check if the file is either a normal file, or, e.g., a fifo
    exists_but_non_dir = os.path.exists(path) and not os.path.isdir(path)
    if os.path.isfile(path) or exists_but_non_dir:
        os.remove(path)
    else:
        shutil.rmtree(path)