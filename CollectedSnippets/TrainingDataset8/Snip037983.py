def get_file(self, filename: str) -> MemoryFile:
        """Return the MemoryFile with the given filename. Filenames are of the
        form "file_id.extension". (Note that this is *not* the optional
        user-specified filename for download files.)

        Raises a MediaFileStorageError if no such file exists.
        """
        file_id = os.path.splitext(filename)[0]
        try:
            return self._files_by_id[file_id]
        except KeyError as e:
            raise MediaFileStorageError(
                f"Bad filename '{filename}'. (No media file with id '{file_id}')"
            ) from e