def _validate_and_resolve_paths(self) -> list[BaseFileComponent.BaseFile]:
        """Override to handle file_path_str input from tool mode and cloud storage.

        Priority:
        1. Cloud storage (AWS/Google Drive) if selected
        2. file_path_str (if provided by the tool call)
        3. path (uploaded file from UI)
        """
        storage_location = self._get_selected_storage_location()

        # Handle AWS S3
        if storage_location == "AWS":
            return self._read_from_aws_s3()

        # Handle Google Drive
        if storage_location == "Google Drive":
            return self._read_from_google_drive()

        # Handle Local storage
        # Check if file_path_str is provided (from tool mode)
        file_path_str = getattr(self, "file_path_str", None)
        if file_path_str:
            # Use the string path from tool mode
            from pathlib import Path

            from lfx.schema.data import Data

            # Use same resolution logic as BaseFileComponent (support storage paths)
            path_str = str(file_path_str)
            if parse_storage_path(path_str):
                try:
                    resolved_path = Path(self.get_full_path(path_str))
                except (ValueError, AttributeError):
                    resolved_path = Path(self.resolve_path(path_str))
            else:
                resolved_path = Path(self.resolve_path(path_str))

            if not resolved_path.exists():
                msg = f"File or directory not found: {file_path_str}"
                self.log(msg)
                if not self.silent_errors:
                    raise ValueError(msg)
                return []

            data_obj = Data(data={self.SERVER_FILE_PATH_FIELDNAME: str(resolved_path)})
            return [BaseFileComponent.BaseFile(data_obj, resolved_path, delete_after_processing=False)]

        # Otherwise use the default implementation (uses path FileInput)
        return super()._validate_and_resolve_paths()