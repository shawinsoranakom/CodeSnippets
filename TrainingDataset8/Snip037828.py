def _write_to_disk_cache(self, key: str, pickled_value: bytes) -> None:
        path = self._get_file_path(key)
        try:
            with streamlit_write(path, binary=True) as output:
                output.write(pickled_value)
        except util.Error as e:
            _LOGGER.debug(e)
            # Clean up file so we don't leave zero byte files.
            try:
                os.remove(path)
            except (FileNotFoundError, IOError, OSError):
                # If we can't remove the file, it's not a big deal.
                pass
            raise CacheError("Unable to write to cache") from e