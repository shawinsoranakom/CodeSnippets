def is_blacklisted(self, filepath):
        """Test if filepath is in the blacklist.

        Parameters
        ----------
        filepath : str
            File path that we intend to test.

        """
        return any(
            file_util.file_is_in_folder_glob(filepath, blacklisted_folder)
            for blacklisted_folder in self._folder_blacklist
        )