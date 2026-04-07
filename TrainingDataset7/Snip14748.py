def __copy__(self):
        obj = self.create(connector=self.connector, negated=self.negated)
        obj.children = self.children  # Don't [:] as .__init__() via .create() does.
        return obj