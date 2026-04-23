def add(
        self,
        path_or_data: Union[bytes, str],
        mimetype: str,
        coordinates: str,
        file_name: Optional[str] = None,
        is_for_static_download: bool = False,
    ) -> str:
        """Add a new MediaFile with the given parameters and return its URL.

        If an identical file already exists, return the existing URL
        and registers the current session as a user.

        Safe to call from any thread.

        Parameters
        ----------
        path_or_data : bytes or str
            If bytes: the media file's raw data. If str: the name of a file
            to load from disk.
        mimetype : str
            The mime type for the file. E.g. "audio/mpeg".
            This string will be used in the "Content-Type" header when the file
            is served over HTTP.
        coordinates : str
            Unique string identifying an element's location.
            Prevents memory leak of "forgotten" file IDs when element media
            is being replaced-in-place (e.g. an st.image stream).
            coordinates should be of the form: "1.(3.-14).5"
        file_name : str or None
            Optional file_name. Used to set the filename in the response header.
        is_for_static_download: bool
            Indicate that data stored for downloading as a file,
            not as a media for rendering at page. [default: False]

        Returns
        -------
        str
            The url that the frontend can use to fetch the media.

        Raises
        ------
        If a filename is passed, any Exception raised when trying to read the
        file will be re-raised.
        """

        session_id = _get_session_id()

        with self._lock:
            kind = (
                MediaFileKind.DOWNLOADABLE
                if is_for_static_download
                else MediaFileKind.MEDIA
            )
            file_id = self._storage.load_and_get_id(
                path_or_data, mimetype, kind, file_name
            )
            metadata = MediaFileMetadata(kind=kind)

            self._file_metadata[file_id] = metadata
            self._files_by_session_and_coord[session_id][coordinates] = file_id

            return self._storage.get_url(file_id)