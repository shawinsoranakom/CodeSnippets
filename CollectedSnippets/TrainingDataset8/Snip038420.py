def get_content(
        cls, abspath: str, start: Optional[int] = None, end: Optional[int] = None
    ):
        _LOGGER.debug("MediaFileHandler: GET %s", abspath)

        try:
            # abspath is the hash as used `get_absolute_path`
            media_file = cls._storage.get_file(abspath)
        except Exception:
            _LOGGER.error("MediaFileHandler: Missing file %s", abspath)
            return None

        _LOGGER.debug(
            "MediaFileHandler: Sending %s file %s", media_file.mimetype, abspath
        )

        # If there is no start and end, just return the full content
        if start is None and end is None:
            return media_file.content

        if start is None:
            start = 0
        if end is None:
            end = len(media_file.content)

        # content is bytes that work just by slicing supplied by start and end
        return media_file.content[start:end]