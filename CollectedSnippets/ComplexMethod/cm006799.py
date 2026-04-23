def _filter_and_mark_files(self, files: list[BaseFile]) -> list[BaseFile]:
        """Validate file types and filter out invalid files.

        Args:
            files (list[BaseFile]): List of BaseFile instances.

        Returns:
            list[BaseFile]: Validated BaseFile instances.

        Raises:
            ValueError: If unsupported files are encountered and `ignore_unsupported_extensions` is False.
        """
        settings = get_settings_service().settings
        is_s3_storage = settings.storage_type == "s3"
        final_files = []
        ignored_files = []

        for file in files:
            # For local storage, verify the path is actually a file
            # For S3 storage, paths are virtual keys that don't exist locally
            if not is_s3_storage and not file.path.is_file():
                self.log(f"Not a file: {file.path.name}")
                continue

            # Validate file extension
            extension = file.path.suffix[1:].lower() if file.path.suffix else ""
            if extension not in self.valid_extensions:
                # For local storage, optionally ignore unsupported extensions
                if not is_s3_storage and self.ignore_unsupported_extensions:
                    ignored_files.append(file.path.name)
                    continue

                msg = f"Unsupported file extension: {file.path.suffix}"
                self.log(msg)
                if not self.silent_errors:
                    raise ValueError(msg)

            final_files.append(file)

        if ignored_files:
            self.log(f"Ignored files: {ignored_files}")

        return final_files