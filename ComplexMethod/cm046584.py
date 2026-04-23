def _check_mutual_exclusivity(self) -> "SeedInspectUploadRequest":
        has_legacy = self.content_base64 is not None
        has_multi = self.file_ids is not None
        if has_legacy and has_multi:
            raise ValueError("Provide either content_base64 or file_ids, not both")
        if not has_legacy and not has_multi:
            raise ValueError("Provide either content_base64 or file_ids")
        if has_multi:
            if len(self.file_ids) == 0:
                raise ValueError("file_ids must not be empty")
            if not self.block_id:
                raise ValueError("block_id is required when using file_ids")
            if self.file_names is None or len(self.file_ids) != len(self.file_names):
                raise ValueError(
                    "file_names must be provided and same length as file_ids"
                )
        if has_legacy:
            if not self.filename:
                raise ValueError("filename is required when using content_base64")
        return self