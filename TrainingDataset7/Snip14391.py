def __str__(self):
        return "%s. You passed in %r (%s)" % (
            super().__str__(),
            self.object,
            type(self.object),
        )