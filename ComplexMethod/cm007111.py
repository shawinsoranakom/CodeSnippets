def load_directory(self) -> list[Data]:
        path = self.path
        types = self.types
        depth = self.depth
        max_concurrency = self.max_concurrency
        load_hidden = self.load_hidden
        recursive = self.recursive
        silent_errors = self.silent_errors
        use_multithreading = self.use_multithreading

        resolved_path = self.resolve_path(path)

        # If no types are specified, use all supported types
        if not types:
            types = TEXT_FILE_TYPES

        # Check if all specified types are valid
        invalid_types = [t for t in types if t not in TEXT_FILE_TYPES]
        if invalid_types:
            msg = f"Invalid file types specified: {invalid_types}. Valid types are: {TEXT_FILE_TYPES}"
            raise ValueError(msg)

        valid_types = types

        file_paths = retrieve_file_paths(
            resolved_path, load_hidden=load_hidden, recursive=recursive, depth=depth, types=valid_types
        )

        loaded_data = []
        if use_multithreading:
            loaded_data = parallel_load_data(file_paths, silent_errors=silent_errors, max_concurrency=max_concurrency)
        else:
            loaded_data = [parse_text_file_to_data(file_path, silent_errors=silent_errors) for file_path in file_paths]

        valid_data = [x for x in loaded_data if x is not None and isinstance(x, Data)]
        self.status = valid_data
        return valid_data