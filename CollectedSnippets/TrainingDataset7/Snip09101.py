def sign(self, value):
        return "%s%s%s" % (value, self.sep, self.signature(value))