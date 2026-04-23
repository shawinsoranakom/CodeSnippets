def __str__(self):
        authors = " and ".join(a.name for a in self.authors.all())
        return "%s by %s" % (self.name, authors) if authors else self.name