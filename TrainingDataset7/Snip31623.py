def get_by_natural_key(self, kind, name):
        return self.get(kind=kind, name=name)