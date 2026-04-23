def get_by_natural_key(self, name, author):
        return self.get(name=name, author__name=author)