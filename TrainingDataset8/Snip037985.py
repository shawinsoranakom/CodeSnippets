def delete_file(self, file_id: str) -> None:
        """Delete the file with the given ID."""
        # We swallow KeyErrors here - it's not an error to delete a file
        # that doesn't exist.
        with contextlib.suppress(KeyError):
            del self._files_by_id[file_id]