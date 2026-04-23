def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        if self.autosummarize is not None:
            kwargs["autosummarize"] = self.autosummarize
        if self.pages_per_range is not None:
            kwargs["pages_per_range"] = self.pages_per_range
        return path, args, kwargs