def __repr__(self):
        alias, target = self.alias, self.target
        identifiers = (alias, str(target)) if alias else (str(target),)
        return "{}({})".format(self.__class__.__name__, ", ".join(identifiers))