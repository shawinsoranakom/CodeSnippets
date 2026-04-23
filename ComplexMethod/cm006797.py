def _validate_and_resolve_paths(self) -> list[BaseFile]:
        """Validate that all input paths exist and are valid, and create BaseFile instances.

        Returns:
            list[BaseFile]: A list of valid BaseFile instances.

        Raises:
            ValueError: If any path does not exist.
        """
        resolved_files = []

        def add_file(data: Data, path: str | Path, *, delete_after_processing: bool):
            path_str = str(path)
            settings = get_settings_service().settings

            # When using object storage (S3), file paths are storage keys (e.g., "<flow_id>/<filename>")
            # that don't exist on the local filesystem. We defer validation until file processing.
            # For local storage, validate the file exists immediately to fail fast.
            if settings.storage_type == "s3":
                resolved_files.append(
                    BaseFileComponent.BaseFile(data, Path(path_str), delete_after_processing=delete_after_processing)
                )
            else:
                # Check if path looks like a storage path (flow_id/filename format)
                # If so, use get_full_path to resolve it to the actual storage location
                if parse_storage_path(path_str):
                    try:
                        resolved_path = Path(self.get_full_path(path_str))
                        self.log(f"Resolved storage path '{path_str}' to '{resolved_path}'")
                    except (ValueError, AttributeError) as e:
                        # Fallback to resolve_path if get_full_path fails
                        self.log(f"get_full_path failed for '{path_str}': {e}, falling back to resolve_path")
                        resolved_path = Path(self.resolve_path(path_str))
                else:
                    resolved_path = Path(self.resolve_path(path_str))

                if not resolved_path.exists():
                    msg = f"File not found: '{path}' (resolved to: '{resolved_path}'). Please upload the file again."
                    self.log(msg)
                    if not self.silent_errors:
                        raise ValueError(msg)
                resolved_files.append(
                    BaseFileComponent.BaseFile(data, resolved_path, delete_after_processing=delete_after_processing)
                )

        file_path = self._file_path_as_list()

        if self.path and not file_path:
            # Wrap self.path into a Data object
            if isinstance(self.path, list):
                for path in self.path:
                    data_obj = Data(data={self.SERVER_FILE_PATH_FIELDNAME: path})
                    add_file(data=data_obj, path=path, delete_after_processing=False)
            else:
                data_obj = Data(data={self.SERVER_FILE_PATH_FIELDNAME: self.path})
                add_file(data=data_obj, path=self.path, delete_after_processing=False)
        elif file_path:
            for obj in file_path:
                server_file_path = obj.data.get(self.SERVER_FILE_PATH_FIELDNAME)
                if server_file_path:
                    add_file(
                        data=obj,
                        path=server_file_path,
                        delete_after_processing=self.delete_server_file_after_processing,
                    )
                elif not self.ignore_unspecified_files:
                    msg = f"Data object missing '{self.SERVER_FILE_PATH_FIELDNAME}' property."
                    self.log(msg)
                    if not self.silent_errors:
                        raise ValueError(msg)
                else:
                    msg = f"Ignoring Data object missing '{self.SERVER_FILE_PATH_FIELDNAME}' property:\n{obj}"
                    self.log(msg)

        return resolved_files