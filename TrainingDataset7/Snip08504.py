def _initialize_times(self):
        self.created_time = now()
        self.accessed_time = self.created_time
        self.modified_time = self.created_time