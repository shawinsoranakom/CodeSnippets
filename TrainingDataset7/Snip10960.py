def __repr__(self):
        return "{}({}, descending={})".format(
            self.__class__.__name__, self.expression, self.descending
        )