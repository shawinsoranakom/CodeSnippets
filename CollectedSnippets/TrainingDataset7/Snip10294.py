def describe(self):
        return "Rename table for %s to %s" % (
            self.name,
            self.table if self.table is not None else "(default)",
        )