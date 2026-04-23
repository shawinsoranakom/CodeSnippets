def is_empty(self):
        return any(isinstance(c, NothingNode) for c in self.where.children)