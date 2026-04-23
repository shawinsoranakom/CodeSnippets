def delete_file(self, file_id: str) -> None:
        """Delete a file from the manager.

        This should be called when a given file is no longer referenced
        by any connected client, so that the MediaFileStorage can free its
        resources.

        Calling `delete_file` on a file_id that doesn't exist is allowed,
        and is a no-op. (This means that multiple `delete_file` calls with
        the same file_id is not an error.)

        Note: implementations can choose to ignore `delete_file` calls -
        this function is a *suggestion*, not a *command*. Callers should
        not rely on file deletion happening immediately (or at all).

        Parameters
        ----------
        file_id
            The file's ID, returned from load_media_and_get_id().

        Returns
        -------
        None

        Raises
        ------
        MediaFileStorageError
            Raised if file deletion fails for any reason. Note that these
            failures will generally not be shown on the frontend (file
            deletion usually occurs on session disconnect).

        """
        raise NotImplementedError