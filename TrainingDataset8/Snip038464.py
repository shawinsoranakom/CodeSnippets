def initialize(
        self, file_mgr: UploadedFileManager, is_active_session: Callable[[str], bool]
    ):
        """
        Parameters
        ----------
        file_mgr : UploadedFileManager
            The server's singleton UploadedFileManager. All file uploads
            go here.
        is_active_session:
            A function that returns true if a session_id belongs to an active
            session.
        """
        self._file_mgr = file_mgr
        self._is_active_session = is_active_session