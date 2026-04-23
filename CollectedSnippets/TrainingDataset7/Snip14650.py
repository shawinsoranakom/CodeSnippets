def __enter__(self):
        self.old_timezone = getattr(_active, "value", None)
        if self.timezone is None:
            deactivate()
        else:
            activate(self.timezone)