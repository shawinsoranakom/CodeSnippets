def _add_file_and_get_object(
        self,
        content: bytes,
        mimetype: str,
        coordinates: str,
        filename: Optional[str] = None,
    ) -> MemoryFile:
        """Add a new file to our test manager and return its MediaFile object."""
        file_id = _calculate_file_id(content, mimetype, filename)
        self.media_file_manager.add(content, mimetype, coordinates, filename)
        return self.storage.get_file(file_id)