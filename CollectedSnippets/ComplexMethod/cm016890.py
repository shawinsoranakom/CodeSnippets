def recursive_search_models_(self, directory: str, pathIndex: int) -> tuple[list[str], dict[str, float], float]:
        if not os.path.isdir(directory):
            return [], {}, time.perf_counter()

        excluded_dir_names = [".git"]
        # TODO use settings
        include_hidden_files = False

        result: list[str] = []
        dirs: dict[str, float] = {}

        for dirpath, subdirs, filenames in os.walk(directory, followlinks=True, topdown=True):
            subdirs[:] = [d for d in subdirs if d not in excluded_dir_names]
            if not include_hidden_files:
                subdirs[:] = [d for d in subdirs if not d.startswith(".")]
                filenames = [f for f in filenames if not f.startswith(".")]

            filenames = filter_files_extensions(filenames, folder_paths.supported_pt_extensions)

            for file_name in filenames:
                try:
                    full_path = os.path.join(dirpath, file_name)
                    relative_path = os.path.relpath(full_path, directory)

                    # Get file metadata
                    file_info = {
                        "name": relative_path,
                        "pathIndex": pathIndex,
                        "modified": os.path.getmtime(full_path),  # Add modification time
                        "created": os.path.getctime(full_path),   # Add creation time
                        "size": os.path.getsize(full_path)        # Add file size
                    }
                    result.append(file_info)

                except Exception as e:
                    logging.warning(f"Warning: Unable to access {file_name}. Error: {e}. Skipping this file.")
                    continue

            for d in subdirs:
                path: str = os.path.join(dirpath, d)
                try:
                    dirs[path] = os.path.getmtime(path)
                except FileNotFoundError:
                    logging.warning(f"Warning: Unable to access {path}. Skipping this path.")
                    continue

        return result, dirs, time.perf_counter()