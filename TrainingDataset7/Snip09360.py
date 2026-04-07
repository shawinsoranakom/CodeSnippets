def skip_default(self, field):
        """
        Some backends don't accept default values for certain columns types
        (i.e. MySQL longtext and longblob).
        """
        return False