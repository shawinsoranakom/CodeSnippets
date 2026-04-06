def load_source(self, monkeypatch):
        monkeypatch.setattr('thefuck.types.load_source',
                            lambda x, _: Rule(x))