def get_modified_time(self, name):
        return self._datetime_from_timestamp(os.path.getmtime(self.path(name)))