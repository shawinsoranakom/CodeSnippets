def load_and_get_id(
        self,
        path_or_data: Union[str, bytes],
        mimetype: str,
        kind: MediaFileKind,
        filename: Optional[str] = None,
    ) -> str:
        """Add a file to the manager and return its ID."""
        file_data: bytes
        if isinstance(path_or_data, str):
            file_data = self._read_file(path_or_data)
        else:
            file_data = path_or_data

        # Because our file_ids are stable, if we already have a file with the
        # given ID, we don't need to create a new one.
        file_id = _calculate_file_id(file_data, mimetype, filename)
        if file_id not in self._files_by_id:
            LOGGER.debug("Adding media file %s", file_id)
            media_file = MemoryFile(
                content=file_data, mimetype=mimetype, kind=kind, filename=filename
            )
            self._files_by_id[file_id] = media_file

        return file_id