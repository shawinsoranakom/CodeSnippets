def __iter__(self):
        yield from normalize_choices(self.func())