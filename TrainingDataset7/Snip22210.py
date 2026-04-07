def __str__(self):
        return "%s by %s (available at %s)" % (
            self.name,
            self.author.name,
            ", ".join(s.name for s in self.stores.all()),
        )