def wipe_tree(path: str) -> None:
    if not os.path.exists(path):
        print(f"Warning: Path not found {path}")
        return
    print(f"Wiping {path}...")
    all_files = os.listdir(path)

    files_to_remove = [file for file in all_files if file != ".gitignore"]
    for file_name in files_to_remove:
        file_path = os.path.join(path, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            print(f" - Deleted {file_path}")
        except PermissionError:
            print(
                f"PermissionError: Unable to remove {file_path}. It is in use by another process."
            )
            continue