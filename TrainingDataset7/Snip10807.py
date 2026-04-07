def desc(self, **kwargs):
        return OrderBy(self, descending=True, **kwargs)