def get_accessed_time(self, name):
        return self._datetime_from_timestamp(os.path.getatime(self.path(name)))