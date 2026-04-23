def loader_name(self):
        if self.loader:
            return "%s.%s" % (
                self.loader.__module__,
                self.loader.__class__.__name__,
            )