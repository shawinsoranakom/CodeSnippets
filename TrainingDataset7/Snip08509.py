def write(self, data):
        super().write(data)
        self._update_modified_time()