def get_url(self, file_id: str) -> str:
        """Return a URL for a file in the manager.

        Parameters
        ----------
        file_id
            The file's ID, returned from load_media_and_get_id().

        Returns
        -------
        str
            A URL that the frontend can load the file from. Because this
            URL may expire, it should not be cached!

        Raises
        ------
        MediaFileStorageError
            Raised if the manager doesn't contain an object with the given ID.

        """
        raise NotImplementedError