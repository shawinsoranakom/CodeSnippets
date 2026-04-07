def get_refs(self):
        refs = set()
        for child in self.children:
            refs |= child.get_refs()
        return refs