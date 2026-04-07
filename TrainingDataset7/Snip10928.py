def __str__(self):
        return "WHEN %r THEN %r" % (self.condition, self.result)