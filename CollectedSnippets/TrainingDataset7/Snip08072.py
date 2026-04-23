def lastmod(self, item):
        if self.date_field is not None:
            return getattr(item, self.date_field)
        return None