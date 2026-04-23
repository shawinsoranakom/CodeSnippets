def __iter__(self):
        for _, nodelist in self.conditions_nodelists:
            yield from nodelist