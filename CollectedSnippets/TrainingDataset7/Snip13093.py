def enqueue(self, *args, **kwargs):
        """Queue up the Task to be executed."""
        return self.get_backend().enqueue(self, args, kwargs)