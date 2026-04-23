def _extract_file_metadata(self, data_item) -> dict:
        """Extract metadata from a data item with file_path."""
        metadata: dict[str, Any] = {}
        if not hasattr(data_item, "file_path"):
            return metadata

        file_path = data_item.file_path
        file_path_obj = Path(file_path)
        filename = file_path_obj.name

        settings = get_settings_service().settings
        if settings.storage_type == "s3":
            try:
                file_size = get_file_size(file_path)
            except (FileNotFoundError, ValueError):
                # If we can't get file size, set to 0 or omit
                file_size = 0
        else:
            try:
                file_size_stat = file_path_obj.stat()
                file_size = file_size_stat.st_size
            except OSError:
                file_size = 0

        # Basic file metadata
        metadata["filename"] = filename
        metadata["file_size"] = file_size

        # Add MIME type from extension
        extension = filename.split(".")[-1]
        if extension:
            metadata["mimetype"] = build_content_type_from_extension(extension)

        # Copy additional metadata from data if available
        if hasattr(data_item, "data") and isinstance(data_item.data, dict):
            metadata_fields = ["mimetype", "file_size", "created_time", "modified_time"]
            for field in metadata_fields:
                if field in data_item.data:
                    metadata[field] = data_item.data[field]

        return metadata