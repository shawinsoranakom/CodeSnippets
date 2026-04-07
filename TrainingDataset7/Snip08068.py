def get_latest_lastmod(self):
        if not hasattr(self, "lastmod"):
            return None
        if callable(self.lastmod):
            try:
                return max([self.lastmod(item) for item in self.items()], default=None)
            except TypeError:
                return None
        else:
            return self.lastmod