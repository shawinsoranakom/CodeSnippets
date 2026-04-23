def __repr__(self):
        return "<%s: extends %s>" % (self.__class__.__name__, self.parent_name.token)