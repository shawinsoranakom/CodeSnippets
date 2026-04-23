def __exit__(self, exc_type, exc_value, traceback):
        self.queryset._enable_cloning()