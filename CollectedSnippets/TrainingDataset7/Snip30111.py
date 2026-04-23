def __str__(self):
        return "%s (%s)" % (
            self.name,
            ", ".join(q.name for q in self.qualifications.all()),
        )