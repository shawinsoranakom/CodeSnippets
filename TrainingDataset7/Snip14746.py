def __str__(self):
        template = "(NOT (%s: %s))" if self.negated else "(%s: %s)"
        return template % (self.connector, ", ".join(str(c) for c in self.children))