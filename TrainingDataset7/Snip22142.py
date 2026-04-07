def __str__(self):
        return "%s %s" % (
            self.person.name,
            ", ".join(p.name for p in self.permissions.all()),
        )