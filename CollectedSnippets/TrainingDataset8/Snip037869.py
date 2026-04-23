def get_message(self, hash: str) -> Optional[ForwardMsg]:
        """Return the message with the given ID if it exists in the cache.

        Parameters
        ----------
        hash : string
            The id of the message to retrieve.

        Returns
        -------
        ForwardMsg | None

        """
        entry = self._entries.get(hash, None)
        return entry.msg if entry else None