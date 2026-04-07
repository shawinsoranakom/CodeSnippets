def count(self):
        """Return the total number of objects, across all pages."""
        c = getattr(self.object_list, "count", None)
        if callable(c) and not inspect.isbuiltin(c) and method_has_no_args(c):
            return c()
        return len(self.object_list)