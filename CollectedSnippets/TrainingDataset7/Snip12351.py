def leaves(self):
        for child in self.children:
            if isinstance(child, WhereNode):
                yield from child.leaves()
            else:
                yield child