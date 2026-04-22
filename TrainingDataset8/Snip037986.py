def _read_file(self, filename: str) -> bytes:
        """Read a file into memory. Raise MediaFileStorageError if we can't."""
        try:
            with open(filename, "rb") as f:
                return f.read()
        except Exception as ex:
            raise MediaFileStorageError(f"Error opening '{filename}'") from ex