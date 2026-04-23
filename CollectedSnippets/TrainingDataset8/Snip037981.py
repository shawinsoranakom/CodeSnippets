def __init__(self, media_endpoint: str):
        """Create a new MemoryMediaFileStorage instance

        Parameters
        ----------
        media_endpoint
            The name of the local endpoint that media is served from.
            This endpoint should start with a forward-slash (e.g. "/media").
        """
        self._files_by_id: Dict[str, MemoryFile] = {}
        self._media_endpoint = media_endpoint