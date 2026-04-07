def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        if self.fillfactor is not None:
            kwargs["fillfactor"] = self.fillfactor
        if self.deduplicate_items is not None:
            kwargs["deduplicate_items"] = self.deduplicate_items
        return path, args, kwargs