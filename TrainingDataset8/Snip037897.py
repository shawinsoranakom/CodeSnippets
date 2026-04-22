def _write_to_disk_cache(key: str, value: Any) -> None:
    path = file_util.get_streamlit_file_path("cache", "%s.pickle" % key)

    try:
        with file_util.streamlit_write(path, binary=True) as output:
            entry = _DiskCacheEntry(value=value)
            pickle.dump(entry, output, pickle.HIGHEST_PROTOCOL)
    except util.Error as e:
        _LOGGER.debug(e)
        # Clean up file so we don't leave zero byte files.
        try:
            os.remove(path)
        except (FileNotFoundError, IOError, OSError):
            # If we can't remove the file, it's not a big deal.
            pass
        raise CacheError("Unable to write to cache: %s" % e)