def validate_absolute_path(self, root: str, absolute_path: str) -> str:
        try:
            self._storage.get_file(absolute_path)
        except MediaFileStorageError:
            _LOGGER.error("MediaFileHandler: Missing file %s", absolute_path)
            raise tornado.web.HTTPError(404, "not found")

        return absolute_path