def get_cols(self):
        return [
            Col(self.alias, target, source)
            for target, source in zip(self.targets, self.sources)
        ]