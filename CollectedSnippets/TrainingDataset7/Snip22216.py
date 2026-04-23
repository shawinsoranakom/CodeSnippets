def __str__(self):
        return "%s: Reference to %s [%s]" % (
            self.text,
            self.nk_fk,
            ", ".join(str(o) for o in self.nk_m2m.all()),
        )