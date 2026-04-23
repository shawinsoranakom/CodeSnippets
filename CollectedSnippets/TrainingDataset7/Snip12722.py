def as_data(self):
        return {f: e.as_data() for f, e in self.items()}