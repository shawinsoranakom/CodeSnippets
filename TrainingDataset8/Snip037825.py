def _read_from_disk_cache(self, key: str) -> bytes:
        path = self._get_file_path(key)
        try:
            with streamlit_read(path, binary=True) as input:
                value = input.read()
                _LOGGER.debug("Disk cache first stage HIT: %s", key)
                # The value is a pickled CachedResult, but we don't unpickle it yet
                # so we can avoid having to repickle it when writing to the mem_cache
                return bytes(value)
        except FileNotFoundError:
            raise CacheKeyNotFoundError("Key not found in disk cache")
        except Exception as ex:
            _LOGGER.error(ex)
            raise CacheError("Unable to read from cache") from ex