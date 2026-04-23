def to_user_metadata(self) -> dict[str, Any]:
        """Convert to user_metadata dict for AssetReference.user_metadata JSON field."""
        data: dict[str, Any] = {
            "filename": self.filename,
            "content_length": self.content_length,
            "format": self.format,
        }
        if self.file_path:
            data["file_path"] = self.file_path
        if self.content_type:
            data["content_type"] = self.content_type

        # Tier 2 fields
        if self.base_model:
            data["base_model"] = self.base_model
        if self.trained_words:
            data["trained_words"] = self.trained_words
        if self.air:
            data["air"] = self.air
        if self.has_preview_images:
            data["has_preview_images"] = True

        # Source provenance
        if self.source_url:
            data["source_url"] = self.source_url
        if self.source_arn:
            data["source_arn"] = self.source_arn
        if self.repo_url:
            data["repo_url"] = self.repo_url
        if self.preview_url:
            data["preview_url"] = self.preview_url
        if self.source_hash:
            data["source_hash"] = self.source_hash

        # HuggingFace
        if self.repo_id:
            data["repo_id"] = self.repo_id
        if self.revision:
            data["revision"] = self.revision
        if self.filepath:
            data["filepath"] = self.filepath
        if self.resolve_url:
            data["resolve_url"] = self.resolve_url

        return data