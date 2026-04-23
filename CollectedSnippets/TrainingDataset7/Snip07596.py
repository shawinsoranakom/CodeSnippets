def _loaded_messages(self):
        """
        Return a list of loaded messages, retrieving them first if they have
        not been loaded yet.
        """
        if not hasattr(self, "_loaded_data"):
            messages, all_retrieved = self._get()
            self._loaded_data = messages or []
        return self._loaded_data