def __getattr__(self, name):
        if name in self.UNITS:
            return self.standard / self.UNITS[name]
        else:
            raise AttributeError("Unknown unit type: %s" % name)