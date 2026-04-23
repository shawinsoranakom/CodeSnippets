def _read_from_disk_cache(key: str) -> Any:
    path = file_util.get_streamlit_file_path("cache", "%s.pickle" % key)
    try:
        with file_util.streamlit_read(path, binary=True) as input:
            entry = pickle.load(input)
            value = entry.value
            _LOGGER.debug("Disk cache HIT: %s", type(value))
    except util.Error as e:
        _LOGGER.error(e)
        raise CacheError("Unable to read from cache: %s" % e)

    except FileNotFoundError:
        raise CacheKeyNotFoundError("Key not found in disk cache")
    return value