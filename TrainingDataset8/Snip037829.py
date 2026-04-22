def _remove_from_disk_cache(self, key: str) -> None:
        """Delete a cache file from disk. If the file does not exist on disk,
        return silently. If another exception occurs, log it. Does not throw.
        """
        path = self._get_file_path(key)
        try:
            os.remove(path)
        except FileNotFoundError:
            # The file is already removed.
            pass
        except Exception as ex:
            _LOGGER.exception(
                "Unable to remove a file from the disk cache", exc_info=ex
            )