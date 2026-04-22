def __init__(self, storage: MediaFileStorage):
        self._storage = storage

        # Dict of [file_id -> MediaFileMetadata]
        self._file_metadata: Dict[str, MediaFileMetadata] = dict()

        # Dict[session ID][coordinates] -> file_id.
        self._files_by_session_and_coord: Dict[
            str, Dict[str, str]
        ] = collections.defaultdict(dict)

        # MediaFileManager is used from multiple threads, so all operations
        # need to be protected with a Lock. (This is not an RLock, which
        # means taking it multiple times from the same thread will deadlock.)
        self._lock = threading.Lock()