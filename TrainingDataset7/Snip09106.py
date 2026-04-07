def sign(self, value):
        value = "%s%s%s" % (value, self.sep, self.timestamp())
        return super().sign(value)