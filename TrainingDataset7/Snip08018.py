def _last_modification(self):
        """
        Return the modification time of the file storing the session's content.
        """
        modification = os.stat(self._key_to_file()).st_mtime
        tz = datetime.UTC if settings.USE_TZ else None
        return datetime.datetime.fromtimestamp(modification, tz=tz)