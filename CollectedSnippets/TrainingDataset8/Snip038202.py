def __init__(self):
        # List of files for a given widget in a given session.
        self._files_by_id: Dict[Tuple[str, str], List[UploadedFileRec]] = {}

        # A counter that generates unique file IDs. Each file ID is greater
        # than the previous ID, which means we can use IDs to compare files
        # by age.
        self._file_id_counter = 1
        self._file_id_lock = threading.Lock()

        # Prevents concurrent access to the _files_by_id dict.
        # In remove_session_files(), we iterate over the dict's keys. It's
        # an error to mutate a dict while iterating; this lock prevents that.
        self._files_lock = threading.Lock()
        self.on_files_updated = Signal(
            doc="""Emitted when a file list is added to the manager or updated.

            Parameters
            ----------
            session_id : str
                The session_id for the session whose files were updated.
            """
        )