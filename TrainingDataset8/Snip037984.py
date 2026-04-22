def get_url(self, file_id: str) -> str:
        """Get a URL for a given media file. Raise a MediaFileStorageError if
        no such file exists.
        """
        media_file = self.get_file(file_id)
        extension = get_extension_for_mimetype(media_file.mimetype)
        return f"{self._media_endpoint}/{file_id}{extension}"