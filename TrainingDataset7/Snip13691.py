def __hash__(self):
        return hash((self.name, *self.attributes))