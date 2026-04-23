def __deepcopy__(self, memodict):
        obj = self.create(connector=self.connector, negated=self.negated)
        obj.children = copy.deepcopy(self.children, memodict)
        return obj